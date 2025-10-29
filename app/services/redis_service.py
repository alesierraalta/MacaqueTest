"""
Servicio Redis para caché de resúmenes y rate limiting.
Implementa graceful degradation si Redis no está disponible.
"""

import hashlib  # Para generar hashes SHA-256 de claves de caché
import json  # Para serializar/deserializar datos JSON
from typing import Dict, Any, Optional  # Tipos de datos
import redis.asyncio as redis  # Cliente asíncrono de Redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError  # Excepciones de Redis
from app.core.config import settings  # Configuración de la aplicación
from app.core.logging import get_logger  # Sistema de logging

logger = get_logger(__name__)


class RedisService:
    """Servicio Redis con caché y rate limiting."""
    
    def __init__(self):
        """Inicializa el cliente Redis."""
        self._client: Optional[redis.Redis] = None  # Cliente Redis asíncrono
        self._is_available: bool = False  # Estado de disponibilidad de Redis
        
        if settings.enable_redis:  # Solo inicializar si Redis está habilitado
            self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente Redis con configuración."""
        try:
            self._client = redis.from_url(
                settings.redis_url,
                socket_timeout=2.0,  # Timeout corto para evitar bloqueos
                socket_connect_timeout=2.0,
                retry_on_timeout=True,
                decode_responses=True
            )
            logger.info(f"Cliente Redis inicializado: {settings.redis_url}")
        except Exception as e:
            logger.warning(f"Error inicializando Redis: {e}")
            self._client = None
    
    async def _ensure_connection(self) -> bool:
        """
        Verifica y establece conexión con Redis.
        
        Returns:
            True si Redis está disponible, False en caso contrario
        """
        if not self._client:
            return False
            
        try:
            await self._client.ping()
            self._is_available = True
            return True
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"Redis no disponible: {e}")
            self._is_available = False
            return False
    
    def generate_cache_key(self, text: str, lang: str, max_tokens: int, tone: str) -> str:
        """
        Genera una clave de caché única basada en el contenido y parámetros.
        
        Args:
            text: Texto a resumir
            lang: Idioma del texto
            max_tokens: Máximo número de tokens
            tone: Tono del resumen
            
        Returns:
            Clave de caché SHA-256
        """
        # Crear string único con todos los parámetros
        cache_data = f"{text}|{lang}|{max_tokens}|{tone}"
        
        # Generar hash SHA-256
        cache_key = hashlib.sha256(cache_data.encode('utf-8')).hexdigest()
        
        # Prefijo para identificar el tipo de caché
        return f"summary:{cache_key}"
    
    async def get_cached_summary(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un resumen del caché.
        
        Args:
            cache_key: Clave del caché
            
        Returns:
            Datos del resumen si existe, None en caso contrario o si Redis falla
        """
        if not await self._ensure_connection():
            return None
            
        try:
            cached_data = await self._client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit para clave: {cache_key[:16]}...")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache miss para clave: {cache_key[:16]}...")
                return None
                
        except (ConnectionError, TimeoutError, RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error obteniendo caché: {e}")
            return None
    
    async def set_cached_summary(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """
        Guarda un resumen en el caché.
        
        Args:
            cache_key: Clave del caché
            data: Datos del resumen
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not await self._ensure_connection():
            return False
            
        try:
            # Serializar datos como JSON
            json_data = json.dumps(data, ensure_ascii=False)
            
            # Guardar con TTL
            await self._client.setex(
                cache_key, 
                settings.cache_ttl_seconds, 
                json_data
            )
            
            logger.info(f"Resumen guardado en caché: {cache_key[:16]}...")
            return True
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.warning(f"Error guardando caché: {e}")
            return False
    
    async def check_rate_limit(self, api_key: str) -> bool:
        """
        Verifica si la API key puede hacer más requests según el rate limit.
        
        Args:
            api_key: API key del cliente
            
        Returns:
            True si puede hacer más requests, False si excedió el límite
        """
        if not await self._ensure_connection():
            # Si Redis no está disponible, permitir el request (graceful degradation)
            logger.warning("Redis no disponible, saltando rate limiting")
            return True
            
        try:
            # Clave para el rate limiting por API key
            rate_key = f"rate_limit:{api_key}"
            
            # Obtener contador actual
            current_count = await self._client.get(rate_key)
            
            if current_count is None:
                # Primera request de esta API key en el último minuto
                await self._client.setex(rate_key, 60, 1)  # TTL de 60 segundos
                logger.debug(f"Rate limit iniciado para API key: {api_key[:8]}...")
                return True
            
            current_count = int(current_count)
            
            if current_count >= settings.rate_limit_requests:
                logger.warning(f"Rate limit excedido para API key: {api_key[:8]}... ({current_count}/{settings.rate_limit_requests})")
                return False
            
            # Incrementar contador
            await self._client.incr(rate_key)
            logger.debug(f"Rate limit incrementado para API key: {api_key[:8]}... ({current_count + 1}/{settings.rate_limit_requests})")
            return True
            
        except (ConnectionError, TimeoutError, RedisError, ValueError) as e:
            logger.warning(f"Error verificando rate limit: {e}")
            # En caso de error, permitir el request (graceful degradation)
            return True
    
    async def is_available(self) -> bool:
        """
        Verifica si Redis está disponible.
        
        Returns:
            True si Redis está disponible, False en caso contrario
        """
        return await self._ensure_connection()
    
    async def close(self):
        """Cierra la conexión con Redis."""
        if self._client:
            try:
                await self._client.close()
                logger.info("Conexión Redis cerrada")
            except Exception as e:
                logger.warning(f"Error cerrando Redis: {e}")


# Instancia global del servicio Redis
redis_service = RedisService()
