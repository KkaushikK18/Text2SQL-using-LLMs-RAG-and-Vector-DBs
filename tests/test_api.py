import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_history():
    response = client.get("/history")
    assert response.status_code == 200
    # Should return a list
    assert isinstance(response.json(), list)

def test_invalid_query_route():
    # Sending GET instead of POST should fail
    response = client.get("/query")
    assert response.status_code == 405
