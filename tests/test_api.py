"""
Unit tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_endpoint_success():
    """Test health check when database is available."""
    with patch('api.main.get_db') as mock_db:
        mock_session = Mock()
        mock_session.execute.return_value = None
        mock_db.return_value.__enter__.return_value = mock_session
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


def test_search_messages_validation():
    """Test search endpoint parameter validation."""
    # Test without query parameter
    response = client.get("/api/search/messages")
    assert response.status_code == 422  # Validation error
    
    # Test with query parameter
    with patch('api.main.get_db') as mock_db:
        mock_session = Mock()
        mock_session.execute.return_value.fetchall.return_value = []
        mock_db.return_value = mock_session
        
        response = client.get("/api/search/messages?query=test")
        assert response.status_code == 200


def test_top_products_endpoint():
    """Test top products endpoint."""
    with patch('api.main.get_db') as mock_db:
        mock_session = Mock()
        mock_session.execute.return_value.fetchall.return_value = []
        mock_db.return_value = mock_session
        
        response = client.get("/api/reports/top-products?limit=5")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_list_channels_endpoint():
    """Test list channels endpoint."""
    with patch('api.main.get_db') as mock_db:
        mock_session = Mock()
        mock_session.execute.return_value.fetchall.return_value = []
        mock_db.return_value = mock_session
        
        response = client.get("/api/channels")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
