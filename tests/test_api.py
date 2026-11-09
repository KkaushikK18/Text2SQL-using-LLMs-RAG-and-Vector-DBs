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

def test_get_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark_accuracy" in data
    assert "ast_validity_rate" in data
    assert data["benchmark_accuracy"] > 80.0

def test_get_schema():
    response = client.get("/schema")
    assert response.status_code == 200
    data = response.json()
    assert "total_tables" in data
    assert data["total_tables"] >= 19
    assert "tables" in data
    assert len(data["tables"]) >= 19
    assert "categories" in data

