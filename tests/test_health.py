"""
Tests para el endpoint de health check.
Verifica el funcionamiento del health check.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


class TestHealthEndpoint:
    """Tests para el endpoint de health check."""
    
    def test_health_check_success(self, client):
        """Test de health check exitoso."""
        with patch('app.services.llm_provider.openai_provider.test_connection') as mock_test:
            mock_test.return_value = True
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "status" in data
            assert "timestamp" in data
            assert "latency_ms" in data
            assert "checks" in data
            assert data["status"] == "ok"
            assert data["checks"]["api"] == "ok"
            assert data["checks"]["llm_provider"] == "ok"
    
    def test_health_check_degraded(self, client):
        """Test de health check con estado degradado."""
        with patch('app.services.llm_provider.openai_provider.test_connection') as mock_test:
            mock_test.return_value = False
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["checks"]["api"] == "ok"
            assert data["checks"]["llm_provider"] == "error"
    
    def test_health_check_openai_error(self, client):
        """Test de health check con error en OpenAI."""
        with patch('app.services.llm_provider.openai_provider.test_connection') as mock_test:
            mock_test.side_effect = Exception("Connection error")
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["checks"]["llm_provider"] == "error"
    
    def test_health_check_response_structure(self, client):
        """Test de estructura de respuesta del health check."""
        with patch('app.services.llm_provider.openai_provider.test_connection') as mock_test:
            mock_test.return_value = True
            
            response = client.get("/v1/healthz")
            data = response.json()
            
            # Verificar campos obligatorios
            required_fields = ["status", "timestamp", "latency_ms", "checks"]
            for field in required_fields:
                assert field in data
            
            # Verificar tipos de datos
            assert isinstance(data["status"], str)
            assert isinstance(data["timestamp"], str)
            assert isinstance(data["latency_ms"], int)
            assert isinstance(data["checks"], dict)
            
            # Verificar valores válidos
            assert data["status"] in ["ok", "degraded", "error"]
            assert data["latency_ms"] >= 0


class TestHealthResponseModel:
    """Tests para el modelo de respuesta de health."""
    
    def test_health_response_creation(self):
        """Test de creación de HealthResponse."""
        from app.models.requests import HealthResponse
        
        response = HealthResponse(
            status="ok",
            timestamp="2024-01-15T10:30:00.000Z",
            latency_ms=45,
            checks={"api": "ok", "llm_provider": "ok"}
        )
        
        assert response.status == "ok"
        assert response.timestamp == "2024-01-15T10:30:00.000Z"
        assert response.latency_ms == 45
        assert response.checks["api"] == "ok"
        assert response.checks["llm_provider"] == "ok"
