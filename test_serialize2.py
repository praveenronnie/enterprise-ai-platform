import sys
sys.path.insert(0, 'backend')
import json
from uuid import uuid4
from pathlib import Path

# Load the already-processed JSON to get docling data
json_path = Path('storage/d31ff576-b713-4fa3-a2e4-6684ea75e293/d31ff576-b713-4fa3-a2e4-6684ea75e293.json')
doc_json = json.loads(json_path.read_text(encoding='utf-8'))

# Reconstruct docling document from JSON
from docling_core.types.doc.document import DoclingDocument
docling_doc = DoclingDocument.model_validate(doc_json)

# Now test the extraction functions with the fixed code
from backend.app.shared.models.models import Document
from backend.app.shared.services.document_processor import (
    _extract_images, _extract_tables, _extract_metadata,
    _extract_text_from_json, _extract_pages,
    _chunk_by_sections, _chunk_hybrid, _has_section_hierarchy
)

doc_id = str(uuid4())
doc = Document(
    document_id=doc_id,
    filename='test.pdf',
    file_size=100,
    file_type='application/pdf',
    checksum='',
    binary_hash='',
)

# Build document
doc.extracted_text = _extract_text_from_json(doc_json)
doc.pages = _extract_pages(docling_doc)
doc.total_pages = docling_doc.num_pages
doc.total_words = len(doc.extracted_text.split())
doc.metadata = _extract_metadata(docling_doc)

print('Extracting images...')
doc.images = _extract_images(docling_doc, doc_id)
doc.has_images = len(doc.images) > 0
print(f'  images: {len(doc.images)}')
for img in doc.images:
    print(f'    caption: type={type(img.caption).__name__}, val={repr(img.caption)[:60]}')
    print(f'    mime_type: type={type(img.mime_type).__name__}, val={img.mime_type}')

print('Extracting tables...')
doc.tables = _extract_tables(docling_doc, doc_id)
doc.has_tables = len(doc.tables) > 0
print(f'  tables: {len(doc.tables)}')

print('Extracting chunks...')
if _has_section_hierarchy(docling_doc):
    doc.chunks = _chunk_by_sections(docling_doc, doc_id)
else:
    doc.chunks = _chunk_hybrid(docling_doc, doc_id)
print(f'  chunks: {len(doc.chunks)}')

doc.binary_hash = str(docling_doc.origin.binary_hash)
doc.file_type = docling_doc.origin.mimetype
doc.chunked = True
doc.processing_metadata = {
    'pipeline': 'ThreadedPdfPipeline',
    'ocr_enabled': 'true',
    'page_images': 'true',
    'picture_images': 'true',
    'table_structure': 'true',
}

# Try serialization
from pydantic import TypeAdapter
ta = TypeAdapter(Document)
try:
    data = ta.dump_json(doc)
    print(f'\n=== SERIALIZATION SUCCESSFUL ===')
    print(f'Response size: {len(data)} bytes')
    print(f'Preview: {data[:500]}')
except Exception as e:
    print(f'\n=== SERIALIZATION FAILED: {e} ===')
    for field_name in Document.model_fields:
        val = getattr(doc, field_name)
        if callable(val):
            print(f'  FIELD "{field_name}" IS A METHOD: {val}')
        else:
            try:
                sub_ta = TypeAdapter(Document.model_fields[field_name].annotation)
                sub_ta.dump_json(val)
            except Exception as e2:
                print(f'  FIELD "{field_name}" (type={type(val).__name__}) FAILS: {e2}')