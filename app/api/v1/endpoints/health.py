"""
Endpoint de health check.
Verifica el estado del servicio y conectividad con OpenAI.
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends
from app.models.requests import HealthResponse
from app.services.llm_provider import openai_provider
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verifica el estado del servicio y conectividad con OpenAI"
)
async def health_check() -> HealthResponse:
    """
    Health check que verifica:
    - Estado del servicio (OK/DEGRADED)
    - Conectividad a OpenAI
    - Tiempo de respuesta
    """
    start_time = time.perf_counter()
    
    # Verificar conectividad con OpenAI
    openai_status = "ok"
    try:
        is_connected = await openai_provider.test_connection()
        if not is_connected:
            openai_status = "error"
    except Exception as e:
        logger.warning(f"Error verificando OpenAI: {e}")
        openai_status = "error"
    
    # Determinar estado general
    if openai_status == "ok":
        status = "ok"
    else:
        status = "degraded"  # Fallback disponible
    
    # Calcular latencia
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    
    # Construir respuesta
    health_response = HealthResponse(
        status=status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        latency_ms=latency_ms,
        checks={
            "api": "ok",
            "llm_provider": openai_status
        }
    )
    
    logger.info(
        f"Health check completado: {status}",
        extra={
            'status': status,
            'latency_ms': latency_ms,
            'openai_status': openai_status
        }
    )
    
    return health_response
