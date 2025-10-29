"""
Middleware personalizado para el microservicio.
Incluye manejo de request_id y otros middlewares necesarios.
"""

import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware para agregar request_id a todas las requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa la request agregando un request_id único."""
        # Generar request_id único
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Agregar request_id al logger context
        logger.info(
            f"Iniciando request: {request.method} {request.url.path}",
            extra={'request_id': request_id, 'endpoint': request.url.path}
        )
        
        # Procesar request
        start_time = time.perf_counter()
        response = await call_next(request)
        end_time = time.perf_counter()
        
        # Calcular latencia
        latency_ms = int((end_time - start_time) * 1000)
        
        # Agregar headers de respuesta
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{latency_ms}ms"
        
        # Loggear finalización del request
        logger.info(
            f"Request completado: {request.method} {request.url.path} - {response.status_code}",
            extra={
                'request_id': request_id,
                'endpoint': request.url.path,
                'latency_ms': latency_ms,
                'status_code': response.status_code
            }
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para agregar headers de seguridad."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa la request agregando headers de seguridad."""
        response = await call_next(request)
        
        # Headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging detallado de requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa la request con logging detallado."""
        # Información de la request
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Loggear inicio de request
        logger.info(
            f"Request recibida: {request.method} {request.url.path}",
            extra={
                'request_id': getattr(request.state, 'request_id', None),
                'endpoint': request.url.path,
                'method': request.method,
                'client_ip': client_ip,
                'user_agent': user_agent
            }
        )
        
        # Procesar request
        response = await call_next(request)
        
        # Loggear respuesta
        logger.info(
            f"Response enviada: {response.status_code}",
            extra={
                'request_id': getattr(request.state, 'request_id', None),
                'endpoint': request.url.path,
                'status_code': response.status_code,
                'content_length': response.headers.get("content-length", 0)
            }
        )
        
        return response
