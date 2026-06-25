"""Shared document processing service for PDF documents using Docling."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker import HybridChunker
from docling_core.types.doc.document import (
    DoclingDocument,
    SectionHeaderItem,
)

from backend.app.shared.models.models import Chunk, Document, Image, Table
from backend.app.platform.config.storage import StorageManager
from backend.app.shared.utils.chunk_differ import assign_chunk_hashes

# Extraction tasks run concurrently via ThreadPoolExecutor (mix of I/O and
# light CPU work). DoclingDocument is read-only during extraction — no
# worker mutates it. Each worker returns its own isolated collection.
# Document assembly is a single sequential step after all workers complete.


def _configure_pipeline() -> ThreadedPdfPipelineOptions:

    return ThreadedPdfPipelineOptions(
        do_ocr=True,
        accelerator_options=AcceleratorOptions(AcceleratorDevice.AUTO),
        generate_picture_images=True,
        images_scale=1.0,
        do_table_structure=True,
    )


def _create_converter() -> DocumentConverter:
    opts = _configure_pipeline()
    return DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=opts),
        },
    )


def _extract_images_parallel(docling_doc: DoclingDocument, document_id) -> list[Image]:
    """Extract images concurrently. Each image is saved in its own thread.
    Final ordering is preserved by image_index for downstream consumers.
    """
    image_dir = StorageManager.images_dir(document_id)

    def _save_one(idx: int, picture) -> Image | None:
        if picture.image is None:
            return None
        pil_img = picture.image.pil_image
        if pil_img is None:
            return None

        page_number = picture.prov[0].page_no if picture.prov else 0
        bbox = picture.prov[0].bbox if picture.prov else None

        image_id = f"{document_id}-img-{idx}"
        filename = f"{image_id}.png"
        file_path = image_dir / filename
        pil_img.save(file_path, format="PNG")

        return Image(
            document_id=document_id,
            image_id=image_id,
            page_number=page_number,
            image_index=idx,
            caption=picture.caption_text(docling_doc),
            width=float(pil_img.width),
            height=float(pil_img.height),
            bounding_box=(
                (
                    float(bbox.l),
                    float(bbox.t),
                    float(bbox.r),
                    float(bbox.b),
                )
                if bbox
                else (0.0, 0.0, 0.0, 0.0)
            ),
            file_path=str(file_path),
            mime_type=(
                picture.image.mimetype()
                if callable(picture.image.mimetype)
                else picture.image.mimetype
            ),
        )

    # Submit all image saves concurrently
    futures = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        for idx, picture in enumerate(docling_doc.pictures):
            futures[executor.submit(_save_one, idx, picture)] = idx

    # Collect results in insertion order (by image_index)
    results = {}
    for future in as_completed(futures):
        idx = futures[future]
        result = future.result()
        if result is not None:
            results[idx] = result

    return [results[idx] for idx in sorted(results)]


def _extract_tables(docling_doc: DoclingDocument, doc_id) -> list[Table]:
    tables: list[Table] = []

    for idx, table_item in enumerate(docling_doc.tables):
        page_number = table_item.prov[0].page_no if table_item.prov else 0
        bbox = table_item.prov[0].bbox if table_item.prov else None

        markdown = table_item.export_to_markdown()
        html = table_item.export_to_html()
        df = table_item.export_to_dataframe()
        csv = df.to_csv(index=False) if df is not None else ""

        tables.append(
            Table(
                document_id=doc_id,
                table_id=f"{doc_id}|{idx}",
                page_number=page_number,
                table_index=idx,
                markdown=markdown,
                html=html,
                csv=csv,
                bounding_box=(
                    (
                        float(bbox.l),
                        float(bbox.t),
                        float(bbox.r),
                        float(bbox.b),
                    )
                    if bbox
                    else (0.0, 0.0, 0.0, 0.0)
                ),
            )
        )

    return tables


def _extract_text(docling_doc: DoclingDocument) -> str:
    return docling_doc.export_to_text()


def _extract_text_from_json(doc_json: dict) -> str:
    return "\n".join(t.get("text", "orig") for t in doc_json.get("texts", []))


def _extract_pages(docling_doc: DoclingDocument) -> list[dict[str, str | int]]:
    pages: list[dict[str, str | int]] = []
    for page_no, page_item in docling_doc.pages.items():
        page_info: dict[str, str | int] = {
            "page_number": page_no,
            "width": int(page_item.size.width),
            "height": int(page_item.size.height),
        }
        pages.append(page_info)
    return pages


def _extract_metadata(docling_doc: DoclingDocument) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if docling_doc.origin:
        if docling_doc.origin.mimetype:
            metadata["mimetype"] = docling_doc.origin.mimetype
        if docling_doc.origin.binary_hash:
            metadata["binary_hash"] = docling_doc.origin.binary_hash
        if docling_doc.origin.filename:
            metadata["filename"] = docling_doc.origin.filename
    return metadata


def _save_doc_json(docling_doc: DoclingDocument, doc_id: str) -> dict:
    """Export Docling document to JSON and persist to storage."""
    doc_json = docling_doc.export_to_dict()
    json_storage_path = StorageManager.doc_json(doc_id)
    with open(json_storage_path, "w", encoding="utf-8") as fp:
        json.dump(doc_json, fp, indent=2)
    return doc_json


def _chunk_by_sections(docling_doc: DoclingDocument, doc_id) -> list[Chunk]:
    chunks: list[Chunk] = []
    current_section: str | None = None
    current_level: int | None = None
    current_text_parts: list[str] = []
    current_page_numbers: set[int] = set()
    chunk_index = 0

    for item, level in docling_doc.iterate_items(with_groups=True):
        if isinstance(item, SectionHeaderItem):
            if current_text_parts:
                chunks.append(
                    Chunk(
                        document_id=doc_id,
                        chunk_id=f"chunk_{chunk_index + 1:04d}",
                        chunk_index=chunk_index,
                        page_numbers=sorted(current_page_numbers),
                        section_title=current_section,
                        heading_level=current_level,
                        text=" ".join(current_text_parts),
                    )
                )
                chunk_index += 1
                current_text_parts = []
                current_page_numbers = set()

            current_section = item.text
            current_level = item.level

        if hasattr(item, "text") and item.text:
            current_text_parts.append(item.text)
            if hasattr(item, "prov") and item.prov:
                current_page_numbers.add(item.prov[0].page_no)

    if current_text_parts:
        chunks.append(
            Chunk(
                document_id=doc_id,
                chunk_id=f"chunk_{chunk_index + 1:04d}",
                chunk_index=chunk_index,
                page_numbers=sorted(current_page_numbers),
                section_title=current_section,
                heading_level=current_level,
                text=" ".join(current_text_parts),
            )
        )

    return chunks


def _chunk_hybrid(docling_doc: DoclingDocument, doc_id) -> list[Chunk]:
    chunker = HybridChunker()
    docling_chunks = chunker.chunk(docling_doc)
    chunks: list[Chunk] = []

    for idx, docling_chunk in enumerate(docling_chunks):
        meta = docling_chunk.meta or {}
        page_numbers: list[int] = []
        section_title: str | None = None
        heading_level: int | None = None

        if "headings" in meta and meta["headings"]:
            heading = meta["headings"][0]
            if isinstance(heading, dict):
                section_title = heading.get("text")
                heading_level = heading.get("level")

        if "page_numbers" in meta:
            page_numbers = meta["page_numbers"]
        elif "prov" in meta:
            for prov in meta["prov"]:
                if isinstance(prov, dict) and "page_no" in prov:
                    page_numbers.append(prov["page_no"])

        chunks.append(
            Chunk(
                document_id=doc_id,
                chunk_id=f"chunk_{idx + 1:04d}",
                chunk_index=idx,
                page_numbers=page_numbers,
                section_title=section_title,
                heading_level=heading_level,
                text=docling_chunk.text,
            )
        )

    return chunks


def _has_section_hierarchy(docling_doc: DoclingDocument) -> bool:
    for item, level in docling_doc.iterate_items(with_groups=True):
        if isinstance(item, SectionHeaderItem):
            return True
    return False


def _extract_chunks_and_headings(
    docling_doc: DoclingDocument, doc_id: str
) -> tuple[list[Chunk], list[str]]:
    """Extract chunks and headings. Checks section hierarchy to decide strategy."""
    if _has_section_hierarchy(docling_doc):
        chunks = _chunk_by_sections(docling_doc, doc_id)
        headings = [c.section_title for c in chunks if c.section_title is not None]
    else:
        chunks = _chunk_hybrid(docling_doc, doc_id)
        headings = []
    return chunks, headings


def process_document(
    file_path: str,
    document: Document,
) -> Document:
    converter = _create_converter()
    result = converter.convert(file_path)

    docling_doc = result.document
    doc_id = document.document_id

    # -----------------------------------------------------------------------
    # Phase 1: Launch all independent extraction tasks concurrently.
    # Each task reads from docling_doc (read-only) and returns its own result.
    # No worker mutates the Document object or any shared mutable collection.
    # -----------------------------------------------------------------------
    with ThreadPoolExecutor(max_workers=6) as executor:
        text_future = executor.submit(_extract_text, docling_doc)
        pages_future = executor.submit(_extract_pages, docling_doc)
        metadata_future = executor.submit(_extract_metadata, docling_doc)
        tables_future = executor.submit(_extract_tables, docling_doc, doc_id)
        images_future = executor.submit(_extract_images_parallel, docling_doc, doc_id)
        chunks_future = executor.submit(
            _extract_chunks_and_headings, docling_doc, doc_id
        )
        json_future = executor.submit(_save_doc_json, docling_doc, doc_id)

    # -----------------------------------------------------------------------
    # Phase 2: Collect all results.  Calling .result() re-raises exceptions
    # from workers with meaningful tracebacks preserved.
    # -----------------------------------------------------------------------
    extracted_text = text_future.result()
    pages = pages_future.result()
    meta = metadata_future.result()
    tables = tables_future.result()
    images = images_future.result()
    chunks, headings = chunks_future.result()
    json_future.result()  # ensure JSON write completed (discard return value)

    # -----------------------------------------------------------------------
    # Phase 3: Assemble the final document in a single sequential step.
    # This is the ONLY place where the Document object is mutated.
    # -----------------------------------------------------------------------
    document.extracted_text = extracted_text
    document.pages = pages
    document.total_pages = len(docling_doc.pages)
    document.metadata = meta
    document.images = images
    document.has_images = len(images) > 0
    document.tables = tables
    document.has_tables = len(tables) > 0
    assign_chunk_hashes(chunks)
    document.chunks = chunks
    document.headings = headings
    document.binary_hash = str(result.document.origin.binary_hash)
    document.file_type = result.document.origin.mimetype
    document.chunked = True
    document.processing_metadata = {
        "pipeline": "ThreadedPdfPipeline",
        "ocr_enabled": "true",
        "page_images": "true",
        "picture_images": "true",
        "table_structure": "true",
    }

    return document
