"""Test document upload and processing with Qdrant integration."""
import asyncio
import io
from pathlib import Path

from backend.app.main import create_app
from fastapi.testclient import TestClient
from backend.app.platform.core.lifespan import _register_services, _register_plugins
from backend.app.plugins.base import registry

print('='*60)
print('DOCUMENT UPLOAD & QDRANT INTEGRATION TEST')
print('='*60)

# Register services and plugins
print('\nInitializing services...')
asyncio.run(_register_services())
_register_plugins()
print(f'  Services and plugins ready.')
print(f'  Plugins: {registry.list_types()}')

app = create_app()
client = TestClient(app)

# Create a minimal valid PDF file for testing
pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
400
%%EOF"""

print('\n' + '='*60)
print('TESTING DOCUMENT UPLOAD')
print('='*60)

# Test document upload
print('\n1. POST /api/v1/documents/upload (with PDF file)')
try:
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {"user_id": "test-user"}
    
    response = client.post("/api/v1/documents/upload", files=files, data=data)
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print(f'   ✓ Document uploaded successfully!')
        print(f'   Document ID: {result.get("document_id", "N/A")}')
        print(f'   Filename: {result.get("filename", "N/A")}')
        print(f'   Status: {result.get("status", "N/A")}')
        
        # Check if chunks were created
        if "chunks_created" in result:
            print(f'   Chunks created: {result["chunks_created"]}')
        if "embeddings_indexed" in result:
            print(f'   Embeddings indexed: {result["embeddings_indexed"]}')
            
    elif response.status_code == 422:
        print(f'   Validation error: {response.json()}')
    else:
        print(f'   Error response: {response.text[:500]}')
        
except Exception as e:
    print(f'   ✗ Exception during upload: {e}')
    import traceback
    traceback.print_exc()

# Test health to ensure services are still running
print('\n2. GET /api/v1/health (verify services after upload)')
response = client.get('/api/v1/health')
print(f'   Status: {response.status_code}')
if response.status_code == 200:
    print(f'   ✓ Services healthy')
else:
    print(f'   ✗ Health check failed')

print('\n' + '='*60)
print('TEST COMPLETE')
print('='*60)