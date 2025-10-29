"""
Módulo de seguridad para autenticación con API Key.
Implementa verificación de API keys usando HTTPBearer.
"""

from typing import List  # Tipo de datos para listas
from fastapi import Security, HTTPException, status  # Seguridad y manejo de errores HTTP
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # Autenticación Bearer
from app.core.config import settings  # Configuración de la aplicación
from app.core.logging import get_logger  # Sistema de logging

logger = get_logger(__name__)

# Configurar HTTPBearer para autenticación con API Key
security = HTTPBearer(
    scheme_name="API Key",  # Nombre del esquema de autenticación
    description="API Key requerida para acceder a los endpoints"  # Descripción para OpenAPI
)


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verifica que la API Key proporcionada sea válida.
    
    Args:
        credentials: Credenciales HTTP con la API Key
        
    Returns:
        API Key validada
        
    Raises:
        HTTPException: Si la API Key es inválida o no autorizada
    """
    api_key = credentials.credentials
    allowed_keys = settings.allowed_api_keys
    
    # Verificar que la API key esté en la lista de permitidas
    if api_key not in allowed_keys:
        logger.warning(
            f"Intento de acceso con API key inválida: {api_key[:8]}...",
            extra={'api_key_prefix': api_key[:8]}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o no autorizada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Loggear acceso exitoso (sin exponer la key completa)
    logger.info(
        f"Acceso autorizado con API key: {api_key[:8]}...",
        extra={'api_key_prefix': api_key[:8]}
    )
    
    return api_key


def get_api_key_dependency():
    """
    Retorna la dependencia de verificación de API key.
    Útil para aplicar en endpoints específicos.
    
    Returns:
        Función de dependencia para FastAPI
    """
    return verify_api_key


# Función auxiliar para verificar API key sin dependencia de FastAPI
def is_valid_api_key(api_key: str) -> bool:
    """
    Verifica si una API key es válida sin usar dependencias de FastAPI.
    Útil para testing o verificaciones manuales.
    
    Args:
        api_key: API key a verificar
        
    Returns:
        True si la API key es válida, False en caso contrario
    """
    return api_key in settings.allowed_api_keys
