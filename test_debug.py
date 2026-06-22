import sys
sys.path.insert(0, 'backend')

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.document_converter import PdfFormatOption

from backend.app.shared.models.models import Document, Image, Table, Chunk
from backend.app.shared.services.document_processor import (
    _extract_images, _extract_tables, _extract_metadata,
    _extract_text_from_json, _extract_pages,
    _chunk_by_sections, _chunk_hybrid, _has_section_hierarchy
)
from uuid import uuid4

opts = ThreadedPdfPipelineOptions(
    do_ocr=True,
    accelerator_options=AcceleratorOptions(AcceleratorDevice.AUTO),
    generate_page_images=True,
    images_scale=1.0,
    do_table_structure=True,
)
converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF],
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)},
)
result = converter.convert('storage/ea96fb6b-16e4-43a3-b936-2018d126abec/documents/genai-principles.pdf')
docling_doc = result.document
doc_id = str(uuid4())

doc_json = docling_doc.export_to_dict()

# Build document step by step and check each field
doc = Document(
    document_id=doc_id,
    filename="test.pdf",
    file_size=100,
    file_type="application/pdf",
    checksum="",
    binary_hash="",
)

# Test extracted_text
extracted_text = _extract_text_from_json(doc_json)
print(f"extracted_text type: {type(extracted_text).__name__}")
doc.extracted_text = extracted_text

# Test pages
pages = _extract_pages(docling_doc)
print(f"pages type: {type(pages).__name__}, len: {len(pages)}")
doc.pages = pages

# Test metadata
metadata = _extract_metadata(docling_doc)
print(f"metadata: {metadata}")
for k, v in metadata.items():
    print(f"  metadata[{k}]: type={type(v).__name__}, callable={callable(v)}")
doc.metadata = metadata

# Test images
images = _extract_images(docling_doc, doc_id)
print(f"images type: {type(images).__name__}, len: {len(images)}")
for img in images:
    print(f"  image caption: type={type(img.caption).__name__}, value={repr(img.caption)[:50]}")
    print(f"  image mime_type: type={type(img.mime_type).__name__}, value={img.mime_type}")
doc.images = images

# Test tables
tables = _extract_tables(docling_doc, doc_id)
print(f"tables type: {type(tables).__name__}, len: {len(tables)}")
doc.tables = tables

# Test chunks
if _has_section_hierarchy(docling_doc):
    chunks = _chunk_by_sections(docling_doc, doc_id)
else:
    chunks = _chunk_hybrid(docling_doc, doc_id)
print(f"chunks type: {type(chunks).__name__}, len: {len(chunks)}")
doc.chunks = chunks

# Set remaining fields
doc.total_pages = docling_doc.num_pages
doc.total_words = len(doc.extracted_text.split())
doc.binary_hash = str(result.document.origin.binary_hash)
doc.file_type = result.document.origin.mimetype
doc.chunked = True
doc.processing_metadata = {
    "pipeline": "ThreadedPdfPipeline",
    "ocr_enabled": "true",
    "page_images": "true",
    "picture_images": "true",
    "table_structure": "true",
}

# Now try to serialize
from pydantic import TypeAdapter
ta = TypeAdapter(Document)
try:
    data = ta.dump_json(doc)
    print("\n=== SERIALIZATION SUCCESSFUL ===")
    print(f"Response size: {len(data)} bytes")
except Exception as e:
    print(f"\n=== SERIALIZATION FAILED: {e} ===")
    # Find which field is problematic
    for field_name, field_info in Document.model_fields.items():
        val = getattr(doc, field_name)
        if callable(val):
            print(f"  FIELD '{field_name}' IS A METHOD: {val}")
        else:
            try:
                # Try serializing just this field
                from pydantic import TypeAdapter
                sub_ta = TypeAdapter(field_info.annotation)
                sub_ta.dump_json(val)
            except Exception as e2:
                print(f"  FIELD '{field_name}' (type={type(val).__name__}) FAILS: {e2}")