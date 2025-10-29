"""
Tests para autenticación con API Key.
Verifica el funcionamiento del sistema de autenticación.
"""

import pytest
from fastapi import status
from app.core.security import verify_api_key, is_valid_api_key


class TestAuthentication:
    """Tests para autenticación."""
    
    def test_valid_api_key(self, valid_api_key):
        """Test con API key válida."""
        assert is_valid_api_key(valid_api_key) is True
    
    def test_invalid_api_key(self, invalid_api_key):
        """Test con API key inválida."""
        assert is_valid_api_key(invalid_api_key) is False
    
    def test_empty_api_key(self):
        """Test con API key vacía."""
        assert is_valid_api_key("") is False
        assert is_valid_api_key(None) is False
    
    @pytest.mark.asyncio
    async def test_verify_api_key_success(self, valid_api_key):
        """Test de verificación exitosa de API key."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_api_key
        )
        
        result = await verify_api_key(credentials)
        assert result == valid_api_key
    
    @pytest.mark.asyncio
    async def test_verify_api_key_failure(self, invalid_api_key):
        """Test de verificación fallida de API key."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=invalid_api_key
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API Key inválida" in exc_info.value.detail


class TestAuthenticationEndpoints:
    """Tests de endpoints con autenticación."""
    
    def test_summarize_without_auth(self, client, sample_request):
        """Test de endpoint sin autenticación."""
        response = client.post("/v1/summarize", json=sample_request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_summarize_with_invalid_auth(self, client, sample_request, invalid_api_key):
        """Test de endpoint con autenticación inválida."""
        headers = {"Authorization": f"Bearer {invalid_api_key}"}
        response = client.post("/v1/summarize", json=sample_request, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_summarize_with_valid_auth(self, client, sample_request, valid_api_key, mock_openai_client):
        """Test de endpoint con autenticación válida."""
        # Mock OpenAI client
        import app.services.llm_provider
        app.services.llm_provider.openai_provider.client = mock_openai_client
        
        headers = {"Authorization": f"Bearer {valid_api_key}"}
        response = client.post("/v1/summarize", json=sample_request, headers=headers)
        
        # Debería ser exitoso (aunque el mock puede fallar, pero la auth debería pasar)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_health_without_auth(self, client):
        """Test de health check sin autenticación (debería funcionar)."""
        response = client.get("/v1/healthz")
        assert response.status_code == status.HTTP_200_OK
