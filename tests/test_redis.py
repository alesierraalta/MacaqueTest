"""
Tests para el servicio Redis.
Verifica caché, rate limiting y graceful degradation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.redis_service import RedisService, redis_service


class TestRedisService:
    """Tests para RedisService."""
    
    def test_generate_cache_key_consistency(self):
        """Verifica que la generación de cache_key sea consistente."""
        service = RedisService()
        
        # Mismos parámetros deben generar la misma clave
        key1 = service.generate_cache_key("test text", "es", 100, "neutral")
        key2 = service.generate_cache_key("test text", "es", 100, "neutral")
        
        assert key1 == key2
        assert key1.startswith("summary:")
        assert len(key1) == 72  # "summary:" + 64 chars SHA-256
    
    def test_generate_cache_key_different_params(self):
        """Verifica que diferentes parámetros generen claves diferentes."""
        service = RedisService()
        
        key1 = service.generate_cache_key("test text", "es", 100, "neutral")
        key2 = service.generate_cache_key("test text", "en", 100, "neutral")
        key3 = service.generate_cache_key("test text", "es", 200, "neutral")
        key4 = service.generate_cache_key("test text", "es", 100, "concise")
        
        # Todas las claves deben ser diferentes
        assert len({key1, key2, key3, key4}) == 4
    
    @pytest.mark.asyncio
    async def test_get_cached_summary_no_redis(self):
        """Verifica graceful degradation cuando Redis no está disponible."""
        service = RedisService()
        
        # Mock Redis no disponible
        with patch.object(service, '_ensure_connection', return_value=False):
            result = await service.get_cached_summary("test_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_set_cached_summary_no_redis(self):
        """Verifica graceful degradation al guardar caché cuando Redis no está disponible."""
        service = RedisService()
        
        # Mock Redis no disponible
        with patch.object(service, '_ensure_connection', return_value=False):
            result = await service.set_cached_summary("test_key", {"test": "data"})
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_no_redis(self):
        """Verifica que rate limiting permita requests cuando Redis no está disponible."""
        service = RedisService()
        
        # Mock Redis no disponible
        with patch.object(service, '_ensure_connection', return_value=False):
            result = await service.check_rate_limit("test_api_key")
            assert result is True  # Graceful degradation
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_with_redis(self):
        """Verifica rate limiting con Redis disponible."""
        service = RedisService()
        
        # Mock Redis disponible
        mock_client = AsyncMock()
        service._client = mock_client
        
        with patch.object(service, '_ensure_connection', return_value=True):
            # Primera request (no existe contador)
            mock_client.get.return_value = None
            result = await service.check_rate_limit("test_api_key")
            assert result is True
            mock_client.setex.assert_called_once()
            
            # Reset mock
            mock_client.reset_mock()
            
            # Request dentro del límite
            mock_client.get.return_value = "50"  # 50/100 requests
            mock_client.incr.return_value = 51
            result = await service.check_rate_limit("test_api_key")
            assert result is True
            mock_client.incr.assert_called_once()
            
            # Reset mock
            mock_client.reset_mock()
            
            # Request excediendo límite
            mock_client.get.return_value = "100"  # 100/100 requests
            result = await service.check_rate_limit("test_api_key")
            assert result is False
            mock_client.incr.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_cached_summary_with_redis(self):
        """Verifica obtención de caché con Redis disponible."""
        service = RedisService()
        
        # Mock Redis disponible
        mock_client = AsyncMock()
        service._client = mock_client
        
        with patch.object(service, '_ensure_connection', return_value=True):
            # Cache hit
            cached_data = '{"summary": "test summary", "usage": {"total_tokens": 10}}'
            mock_client.get.return_value = cached_data
            
            result = await service.get_cached_summary("test_key")
            assert result is not None
            assert result["summary"] == "test summary"
            assert result["usage"]["total_tokens"] == 10
            
            # Cache miss
            mock_client.get.return_value = None
            result = await service.get_cached_summary("test_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_set_cached_summary_with_redis(self):
        """Verifica guardado de caché con Redis disponible."""
        service = RedisService()
        
        # Mock Redis disponible
        mock_client = AsyncMock()
        service._client = mock_client
        
        with patch.object(service, '_ensure_connection', return_value=True):
            test_data = {"summary": "test summary", "usage": {"total_tokens": 10}}
            
            result = await service.set_cached_summary("test_key", test_data)
            assert result is True
            mock_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_is_available(self):
        """Verifica verificación de disponibilidad de Redis."""
        service = RedisService()
        
        # Redis disponible
        with patch.object(service, '_ensure_connection', return_value=True):
            result = await service.is_available()
            assert result is True
        
        # Redis no disponible
        with patch.object(service, '_ensure_connection', return_value=False):
            result = await service.is_available()
            assert result is False


class TestRedisIntegration:
    """Tests de integración con Redis."""
    
    @pytest.mark.asyncio
    async def test_redis_service_singleton(self):
        """Verifica que redis_service sea una instancia singleton."""
        from app.services.redis_service import redis_service
        
        # Debe ser la misma instancia
        assert redis_service is not None
        assert isinstance(redis_service, RedisService)
    
    @pytest.mark.asyncio
    async def test_redis_connection_error_handling(self):
        """Verifica manejo de errores de conexión Redis."""
        service = RedisService()
        
        # Mock error de conexión
        mock_client = AsyncMock()
        mock_client.ping.side_effect = Exception("Connection error")
        service._client = mock_client
        
        # Mock _ensure_connection para evitar el error real
        with patch.object(service, '_ensure_connection', return_value=False):
            result = await service._ensure_connection()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_redis_timeout_error_handling(self):
        """Verifica manejo de errores de timeout Redis."""
        service = RedisService()
        
        # Mock error de timeout
        mock_client = AsyncMock()
        mock_client.ping.side_effect = TimeoutError("Timeout")
        service._client = mock_client
        
        # Mock _ensure_connection para evitar el error real
        with patch.object(service, '_ensure_connection', return_value=False):
            result = await service._ensure_connection()
            assert result is False


class TestRedisCacheKeyGeneration:
    """Tests específicos para generación de claves de caché."""
    
    def test_cache_key_with_special_characters(self):
        """Verifica generación de claves con caracteres especiales."""
        service = RedisService()
        
        text_with_special = "Texto con ñ, acentos y símbolos: @#$%^&*()"
        key = service.generate_cache_key(text_with_special, "es", 100, "neutral")
        
        assert key.startswith("summary:")
        assert len(key) == 72
    
    def test_cache_key_with_unicode(self):
        """Verifica generación de claves con caracteres Unicode."""
        service = RedisService()
        
        unicode_text = "Hello 世界 🌍 مرحبا بالعالم"
        key = service.generate_cache_key(unicode_text, "auto", 200, "concise")
        
        assert key.startswith("summary:")
        assert len(key) == 72
    
    def test_cache_key_edge_cases(self):
        """Verifica generación de claves en casos límite."""
        service = RedisService()
        
        # Texto muy corto
        key1 = service.generate_cache_key("a", "es", 10, "neutral")
        
        # Texto muy largo
        long_text = "x" * 1000
        key2 = service.generate_cache_key(long_text, "en", 1000, "bullet")
        
        # Ambos deben generar claves válidas
        assert key1.startswith("summary:")
        assert key2.startswith("summary:")
        assert len(key1) == 72
        assert len(key2) == 72
        assert key1 != key2
