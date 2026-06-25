from backend.app.main import create_app
from fastapi.testclient import TestClient
from backend.app.plugins.base import registry
from backend.app.plugins.manifest import ManifestManager
from backend.app.platform.core.lifespan import _register_plugins

print('Pre-test registry state:')
print(f'  Registry length: {len(registry)}')

manifest = ManifestManager()
entries = manifest.load()
print(f'  Manifest entries: {len(entries)}')

# Manually register plugins before creating app
print('\nManually registering plugins...')
_register_plugins()
print(f'  Registry length after registration: {len(registry)}')
print(f'  Plugin types: {registry.list_types()}')

app = create_app()
client = TestClient(app)

print('\nTesting endpoints...')

# Test health endpoint
response = client.get('/api/v1/health')
print(f'GET /api/v1/health: {response.status_code}')

# Test plugins list
response = client.get('/api/v1/plugins')
print(f'GET /api/v1/plugins: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    total = data.get('total', 0)
    print(f'  Total plugins: {total}')
    for p in data.get('plugins', []):
        print(f'  - {p["plugin_type"]}: {p["display_name"]}')

# Test get specific plugin
response = client.get('/api/v1/plugins/resume')
print(f'GET /api/v1/plugins/resume: {response.status_code}')

response = client.get('/api/v1/plugins/logistics')
print(f'GET /api/v1/plugins/logistics: {response.status_code}')

print('\nAll endpoint tests completed!')