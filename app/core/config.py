"""
Configuración del microservicio usando Pydantic Settings.
Implementa el patrón 12-factor app para configuración.
"""

from typing import List  # Tipo de datos para listas
from pydantic import Field, field_validator  # Validación de campos Pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict  # Configuración 12-factor


class Settings(BaseSettings):
    """Configuración del microservicio de summarización."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # API Keys permitidas (separadas por coma)
    api_keys_allowed: str = Field(
        ..., 
        alias="API_KEYS_ALLOWED",
        description="API Keys permitidas separadas por coma"
    )
    
    # Configuración del proveedor LLM
    llm_provider: str = Field(
        default="openai", 
        description="Proveedor LLM a utilizar"
    )
    openai_api_key: str = Field(
        ..., 
        alias="OPENAI_API_KEY",
        description="API Key de OpenAI"
    )
    openai_model: str = Field(
        default="gpt-5-nano", 
        alias="OPENAI_MODEL",
        description="Modelo de OpenAI a utilizar"
    )
    
    # Configuración de summarización
    summary_max_tokens: int = Field(
        default=500, 
        ge=10, 
        le=2000, 
        description="Máximo número de tokens para el resumen"
    )
    lang_default: str = Field(
        default="auto", 
        description="Idioma por defecto"
    )
    max_text_length: int = Field(
        default=50000, 
        ge=100, 
        le=100000, 
        description="Longitud máxima del texto de entrada"
    )
    
    # Configuración de timeouts y retries
    request_timeout_ms: int = Field(
        default=10000, 
        ge=1000, 
        le=60000, 
        description="Timeout del request en milisegundos"
    )
    llm_timeout_ms: int = Field(
        default=8000, 
        ge=1000, 
        le=30000, 
        description="Timeout de llamada LLM en milisegundos"
    )
    max_retries: int = Field(
        default=2, 
        ge=0, 
        le=5, 
        description="Máximo número de reintentos"
    )
    
    # Configuración de CORS
    cors_origins: str = Field(
        default="*", 
        description="Orígenes permitidos para CORS"
    )
    
    # Configuración de logging
    log_level: str = Field(
        default="INFO", 
        description="Nivel de logging"
    )
    
    # Configuración de Redis (opcional)
    enable_redis: bool = Field(
        default=True,
        description="Habilitar Redis para caché y rate limiting"
    )
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="URL de conexión a Redis"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Tiempo de vida del caché en segundos"
    )
    rate_limit_requests: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Máximo de requests por minuto por API key"
    )
    
    @field_validator('api_keys_allowed')
    @classmethod
    def validate_api_keys(cls, v: str) -> str:
        """Valida que se proporcionen API keys."""
        if not v or not v.strip():
            raise ValueError("API_KEYS_ALLOWED no puede estar vacío")
        return v.strip()
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Valida que se proporcione la API key de OpenAI."""
        if not v or not v.strip():
            raise ValueError("OPENAI_API_KEY es requerida")
        if not v.startswith('sk-'):
            raise ValueError("OPENAI_API_KEY debe comenzar con 'sk-'")
        return v.strip()
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valida el nivel de logging."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL debe ser uno de: {valid_levels}")
        return v.upper()
    
    @property
    def allowed_api_keys(self) -> List[str]:
        """Retorna lista de API keys permitidas."""
        return [key.strip() for key in self.api_keys_allowed.split(',') if key.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de orígenes CORS."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


# Instancia global de configuración
settings = Settings()
