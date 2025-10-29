"""
Endpoint de summarización.
Procesa texto y genera resúmenes usando LLM con fallback extractivo.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.models.requests import SummarizeRequest, SummarizeResponse
from app.services.llm_provider import openai_provider
from app.services.fallback import extractive_fallback
from app.core.security import verify_api_key
from app.core.logging import get_logger, log_summarization, log_error

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Generar Resumen",
    description="Genera un resumen del texto proporcionado usando LLM con fallback extractivo"
)
async def summarize_text(
    request: SummarizeRequest,
    api_key: str = Depends(verify_api_key),
    http_request: Request = None
) -> SummarizeResponse:
    """
    Genera un resumen del texto usando OpenAI con fallback TextRank.
    
    Args:
        request: Datos del request de summarización
        api_key: API key validada
        http_request: Request HTTP para obtener request_id
        
    Returns:
        Resumen generado con metadata
        
    Raises:
        HTTPException: Si hay error en el procesamiento
    """
    start_time = time.perf_counter()
    request_id = getattr(http_request.state, 'request_id', None)
    fallback_used = False
    
    try:
        logger.info(
            f"Iniciando summarización",
            extra={
                'request_id': request_id,
                'text_length': len(request.text),
                'lang': request.lang,
                'max_tokens': request.max_tokens,
                'tone': request.tone
            }
        )
        
        # Intentar generar resumen con OpenAI
        try:
            result = await openai_provider.generate_summary(
                text=request.text,
                lang=request.lang,
                max_tokens=request.max_tokens,
                tone=request.tone
            )
            
            logger.info(
                f"Resumen generado con OpenAI exitosamente",
                extra={
                    'request_id': request_id,
                    'model': result['model'],
                    'tokens_used': result['usage']
                }
            )
            
        except Exception as e:
            logger.warning(
                f"Error con OpenAI, activando fallback: {e}",
                extra={
                    'request_id': request_id,
                    'error_type': type(e).__name__,
                    'fallback_triggered': True
                }
            )
            
            # Activar fallback extractivo
            result = extractive_fallback.generate_summary(
                text=request.text,
                lang=request.lang
            )
            fallback_used = True
            
            logger.info(
                f"Resumen generado con fallback",
                extra={
                    'request_id': request_id,
                    'method': result['method'],
                    'fallback_used': True
                }
            )
        
        # Calcular latencia total
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Construir respuesta
        response = SummarizeResponse(
            summary=result['summary'],
            usage=result['usage'],
            model=result['model'],
            latency_ms=latency_ms,
            fallback_used=fallback_used
        )
        
        # Loggear resumen exitoso
        log_summarization(
            logger=logger,
            request_id=request_id,
            latency_ms=latency_ms,
            model_used=result['model'],
            tokens_used=result['usage'],
            fallback_used=fallback_used
        )
        
        return response
        
    except Exception as e:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Loggear error
        log_error(
            logger=logger,
            request_id=request_id,
            error=e,
            endpoint="/v1/summarize"
        )
        
        # Retornar error HTTP apropiado
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor durante la summarización"
            )
