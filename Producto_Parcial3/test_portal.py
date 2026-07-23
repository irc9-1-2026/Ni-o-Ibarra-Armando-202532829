import pytest
from portal_app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Verifica que la página principal responda correctamente (200 OK)."""
    response = client.get('/')
    assert response.status_code == 200

def test_health_check_route(client):
    """Verifica que el endpoint /health devuelva estado JSON."""
    response = client.get('/health')
    assert response.status_code in [200, 503]
    json_data = response.get_json()
    assert "status" in json_data