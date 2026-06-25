import asyncio
from backend.app.main import create_app
from fastapi.testclient import TestClient
from backend.app.plugins.base import registry
from backend.app.plugins.manifest import ManifestManager
from backend.app.platform.core.lifespan import _register_plugins, _register_services

print('='*60)
print('COMPREHENSIVE ENDPOINT TESTING')
print('='*60)

# Manually register services and plugins before creating app
print('\nRegistering services...')
asyncio.run(_register_services())
print(f'  Services registered.')

print('\nRegistering plugins...')
_register_plugins()
print(f'  Registry length: {len(registry)}')
print(f'  Plugin types: {registry.list_types()}')

app = create_app()
client = TestClient(app)

print('\n' + '='*60)
print('TESTING ENDPOINTS')
print('='*60)

# Test 1: Health endpoint
print('\n1. GET /api/v1/health')
response = client.get('/api/v1/health')
print(f'   Status: {response.status_code}')
if response.status_code == 200:
    print(f'   Response: {response.json()}')
else:
    print(f'   Error: {response.text}')

# Test 2: Version endpoint
print('\n2. GET /api/v1/version')
response = client.get('/api/v1/version')
print(f'   Status: {response.status_code}')
if response.status_code == 200:
    print(f'   Response: {response.json()}')
else:
    print(f'   Error: {response.text}')

# Test 3: List plugins
print('\n3. GET /api/v1/plugins')
response = client.get('/api/v1/plugins')
print(f'   Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'   Total plugins: {data.get("total", 0)}')
    for p in data.get('plugins', []):
        print(f'   - {p["plugin_type"]}: {p["display_name"]}')
else:
    print(f'   Error: {response.text}')

# Test 4: Get specific plugin
print('\n4. GET /api/v1/plugins/resume')
response = client.get('/api/v1/plugins/resume')
print(f'   Status: {response.status_code}')
if response.status_code == 200:
    print(f'   Response: {response.json()}')
else:
    print(f'   Error: {response.text}')

# Test 5: AI Chat endpoint
print('\n5. POST /api/v1/ai/chat')
try:
    response = client.post('/api/v1/ai/chat', json={
        "message": "Hello, this is a test message"
    })
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        print(f'   Response: {response.json()}')
    else:
        print(f'   Error: {response.text}')
except Exception as e:
    print(f'   Exception: {e}')

# Test 6: Chat endpoint
print('\n6. POST /api/v1/chat')
try:
    response = client.post('/api/v1/chat', json={
        "message": "What is this document about?",
        "top_k": 5,
        "include_graph": True
    })
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        print(f'   Response: {response.json()}')
    else:
        print(f'   Error: {response.text}')
except Exception as e:
    print(f'   Exception: {e}')

# Test 7: Chat analyze endpoint
print('\n7. POST /api/v1/chat/analyze')
try:
    response = client.post('/api/v1/chat/analyze', json={
        "question": "Summarize this document",
        "document_id": "test-doc-id"
    })
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        print(f'   Response: {response.json()}')
    else:
        print(f'   Error: {response.text}')
except Exception as e:
    print(f'   Exception: {e}')

# Test 8: Chat compare endpoint
print('\n8. POST /api/v1/chat/compare')
try:
    response = client.post('/api/v1/chat/compare', json={
        "question": "Compare these documents",
        "document_ids": ["doc1", "doc2"]
    })
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        print(f'   Response: {response.json()}')
    else:
        print(f'   Error: {response.text}')
except Exception as e:
    print(f'   Exception: {e}')

# Test 9: Document upload endpoint (without actual file)
print('\n9. POST /api/v1/documents/upload')
try:
    response = client.post('/api/v1/documents/upload')
    print(f'   Status: {response.status_code}')
    if response.status_code != 422:  # 422 is expected for missing file
        print(f'   Response: {response.json()}')
    else:
        print(f'   Expected validation error (422) for missing file')
except Exception as e:
    print(f'   Exception: {e}')

print('\n' + '='*60)
print('TESTING COMPLETE')
print('='*60)