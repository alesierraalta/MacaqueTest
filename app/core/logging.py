"""
Configuración de logging estructurado JSON.
Proporciona logs estructurados para monitoreo y análisis.
"""

import logging  # Sistema de logging de Python
import sys  # Para stdout/stderr
from datetime import datetime  # Para timestamps
from typing import Any, Dict, Optional  # Tipos de datos
from pythonjsonlogger import jsonlogger  # Formatter JSON para logs


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter personalizado para logs JSON estructurados."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Agrega campos personalizados al log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Campos obligatorios
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Campos opcionales
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        if hasattr(record, 'endpoint'):
            log_record['endpoint'] = record.endpoint
            
        if hasattr(record, 'latency_ms'):
            log_record['latency_ms'] = record.latency_ms
            
        if hasattr(record, 'model_used'):
            log_record['model_used'] = record.model_used
            
        if hasattr(record, 'tokens_used'):
            log_record['tokens_used'] = record.tokens_used
            
        if hasattr(record, 'fallback_used'):
            log_record['fallback_used'] = record.fallback_used


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configura el sistema de logging con formato JSON estructurado.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Crear handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level))
    
    # Configurar formatter JSON
    formatter = CustomJsonFormatter(
        fmt='%(timestamp)s %(level)s %(logger)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
    )
    handler.setFormatter(formatter)
    
    # Agregar handler al logger raíz
    root_logger.addHandler(handler)
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_request(
    logger: logging.Logger,
    request_id: str,
    endpoint: str,
    latency_ms: int,
    **kwargs: Any
) -> None:
    """
    Loggea información de un request de manera estructurada.
    
    Args:
        logger: Logger a utilizar
        request_id: ID único del request
        endpoint: Endpoint llamado
        latency_ms: Latencia en milisegundos
        **kwargs: Campos adicionales para el log
    """
    extra = {
        'request_id': request_id,
        'endpoint': endpoint,
        'latency_ms': latency_ms,
        **kwargs
    }
    
    logger.info(
        f"Request completado: {endpoint}",
        extra=extra
    )


def log_summarization(
    logger: logging.Logger,
    request_id: str,
    latency_ms: int,
    model_used: str,
    tokens_used: Dict[str, int],
    fallback_used: bool = False,
    **kwargs: Any
) -> None:
    """
    Loggea información de una operación de summarización.
    
    Args:
        logger: Logger a utilizar
        request_id: ID único del request
        latency_ms: Latencia en milisegundos
        model_used: Modelo utilizado
        tokens_used: Diccionario con tokens utilizados
        fallback_used: Si se usó fallback
        **kwargs: Campos adicionales para el log
    """
    extra = {
        'request_id': request_id,
        'latency_ms': latency_ms,
        'model_used': model_used,
        'tokens_used': tokens_used,
        'fallback_used': fallback_used,
        **kwargs
    }
    
    logger.info(
        f"Summarización completada con modelo {model_used}",
        extra=extra
    )


def log_error(
    logger: logging.Logger,
    request_id: Optional[str],
    error: Exception,
    endpoint: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Loggea errores de manera estructurada.
    
    Args:
        logger: Logger a utilizar
        request_id: ID único del request (opcional)
        error: Excepción ocurrida
        endpoint: Endpoint donde ocurrió el error (opcional)
        **kwargs: Campos adicionales para el log
    """
    extra = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        **kwargs
    }
    
    if request_id:
        extra['request_id'] = request_id
        
    if endpoint:
        extra['endpoint'] = endpoint
    
    logger.error(
        f"Error en {endpoint or 'aplicación'}: {error}",
        extra=extra,
        exc_info=True
    )
