"""
Configuración de tests para pytest.
Define fixtures comunes y configuración de testing.
"""

import pytest  # Framework de testing
import asyncio  # Para operaciones asíncronas en tests
from unittest.mock import AsyncMock, MagicMock  # Mocks para testing
from fastapi.testclient import TestClient  # Cliente de testing síncrono
from httpx import AsyncClient  # Cliente de testing asíncrono
from app.main import app  # Aplicación FastAPI
from app.core.config import settings  # Configuración de la aplicación


@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para toda la sesión de tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Cliente de prueba síncrono."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Cliente de prueba asíncrono."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_api_key():
    """API key válida para testing."""
    return settings.allowed_api_keys[0]


@pytest.fixture
def invalid_api_key():
    """API key inválida para testing."""
    return "invalid-key-123"


@pytest.fixture
def mock_openai_response():
    """Mock de respuesta exitosa de OpenAI."""
    return {
        "summary": "Este es un resumen de prueba generado por OpenAI.",
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70
        },
        "model": "gpt-5-nano"
    }


@pytest.fixture
def mock_openai_client():
    """Mock del cliente OpenAI."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Resumen de prueba"
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 70
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_text():
    """Texto de ejemplo para testing."""
    return """
    Este es un texto de ejemplo para testing del microservicio de summarización.
    Contiene múltiples oraciones para probar la funcionalidad de resumen.
    El texto debe ser lo suficientemente largo para generar un resumen significativo.
    También incluye información adicional para evaluar la calidad del resumen.
    """


@pytest.fixture
def sample_request():
    """Request de ejemplo para testing."""
    return {
        "text": "Este es un texto de ejemplo para testing del microservicio.",
        "lang": "es",
        "max_tokens": 100,
        "tone": "neutral"
    }
