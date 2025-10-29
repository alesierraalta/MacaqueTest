"""
Tests para el endpoint de summarización.
Verifica el funcionamiento del endpoint principal.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


class TestSummarizeEndpoint:
    """Tests para el endpoint de summarización."""
    
    def test_summarize_success(self, client, sample_request, valid_api_key, mock_openai_response):
        """Test de summarización exitosa."""
        with patch('app.services.llm_provider.openai_provider.generate_summary') as mock_generate:
            mock_generate.return_value = mock_openai_response
            
            headers = {"Authorization": f"Bearer {valid_api_key}"}
            response = client.post("/v1/summarize", json=sample_request, headers=headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "summary" in data
            assert "usage" in data
            assert "model" in data
            assert "latency_ms" in data
            assert "fallback_used" in data
            assert data["fallback_used"] is False
    
    def test_summarize_with_fallback(self, client, sample_request, valid_api_key):
        """Test de summarización con fallback."""
        with patch('app.services.llm_provider.openai_provider.generate_summary') as mock_generate:
            # Simular error en OpenAI
            mock_generate.side_effect = Exception("OpenAI error")
            
            headers = {"Authorization": f"Bearer {valid_api_key}"}
            response = client.post("/v1/summarize", json=sample_request, headers=headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "summary" in data
            assert data["fallback_used"] is True
            assert "TextRank" in data["model"]
    
    def test_summarize_validation_error(self, client, valid_api_key):
        """Test de error de validación."""
        invalid_request = {
            "text": "",  # Texto vacío
            "lang": "es",
            "max_tokens": 100,
            "tone": "neutral"
        }
        
        headers = {"Authorization": f"Bearer {valid_api_key}"}
        response = client.post("/v1/summarize", json=invalid_request, headers=headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_summarize_invalid_lang(self, client, valid_api_key):
        """Test con idioma inválido."""
        invalid_request = {
            "text": "Texto de prueba",
            "lang": "invalid_lang",
            "max_tokens": 100,
            "tone": "neutral"
        }
        
        headers = {"Authorization": f"Bearer {valid_api_key}"}
        response = client.post("/v1/summarize", json=invalid_request, headers=headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_summarize_invalid_tone(self, client, valid_api_key):
        """Test con tono inválido."""
        invalid_request = {
            "text": "Texto de prueba",
            "lang": "es",
            "max_tokens": 100,
            "tone": "invalid_tone"
        }
        
        headers = {"Authorization": f"Bearer {valid_api_key}"}
        response = client.post("/v1/summarize", json=invalid_request, headers=headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_summarize_text_too_long(self, client, valid_api_key):
        """Test con texto demasiado largo."""
        long_text = "a" * 50001  # Excede el límite de 50k caracteres
        
        invalid_request = {
            "text": long_text,
            "lang": "es",
            "max_tokens": 100,
            "tone": "neutral"
        }
        
        headers = {"Authorization": f"Bearer {valid_api_key}"}
        response = client.post("/v1/summarize", json=invalid_request, headers=headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_summarize_max_tokens_out_of_range(self, client, valid_api_key):
        """Test con max_tokens fuera de rango."""
        invalid_request = {
            "text": "Texto de prueba",
            "lang": "es",
            "max_tokens": 5,  # Muy bajo
            "tone": "neutral"
        }
        
        headers = {"Authorization": f"Bearer {valid_api_key}"}
        response = client.post("/v1/summarize", json=invalid_request, headers=headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSummarizeRequestValidation:
    """Tests para validación de requests."""
    
    def test_valid_request(self, sample_request):
        """Test de request válido."""
        from app.models.requests import SummarizeRequest
        
        request = SummarizeRequest(**sample_request)
        assert request.text == sample_request["text"]
        assert request.lang == sample_request["lang"]
        assert request.max_tokens == sample_request["max_tokens"]
        assert request.tone == sample_request["tone"]
    
    def test_default_values(self):
        """Test de valores por defecto."""
        from app.models.requests import SummarizeRequest
        
        request = SummarizeRequest(text="Texto de prueba")
        assert request.lang == "auto"
        assert request.max_tokens == 100
        assert request.tone == "neutral"
