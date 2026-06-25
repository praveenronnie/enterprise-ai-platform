import sys
sys.path.insert(0, 'backend')

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.document_converter import PdfFormatOption

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
doc = result.document

# Check origin attributes
print('=== ORIGIN ===')
print(f'type(mimetype)={type(doc.origin.mimetype)} value={doc.origin.mimetype}')
print(f'type(binary_hash)={type(doc.origin.binary_hash)} value={doc.origin.binary_hash}')
print(f'type(filename)={type(doc.origin.filename)} value={doc.origin.filename}')

# Check if any are methods
for attr in ['mimetype', 'binary_hash', 'filename']:
    val = getattr(doc.origin, attr)
    if callable(val):
        print(f'{attr} IS CALLABLE, calling it: {val()}')
    else:
        print(f'{attr} is NOT callable, value: {val}')

# Check pictures
print('=== PICTURES ===')
if doc.pictures:
    pic = doc.pictures[0]
    print(f'type(caption_text)={type(pic.caption_text)}')
    if pic.image:
        print(f'type(mimetype)={type(pic.image.mimetype)}')
        print(f'mimetype={pic.image.mimetype}')
        if callable(pic.image.mimetype):
            print(f'CALLED mimetype={pic.image.mimetype()}')
else:
    print('No pictures found')

# Check texts in dict
doc_json = doc.export_to_dict()
print('=== DICT KEYS ===')
print(list(doc_json.keys()))
print('texts type:', type(doc_json.get('texts', 'NOT_FOUND')))
if 'texts' in doc_json and doc_json['texts']:
    t = doc_json['texts'][0]
    print(f'text item type={type(t)}, keys={list(t.keys()) if isinstance(t, dict) else "N/A"}')