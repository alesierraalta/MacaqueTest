"""
Modelos Pydantic para requests y responses de la API.
Define la estructura de datos para los endpoints del microservicio.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator


class SummarizeRequest(BaseModel):
    """Request para el endpoint de summarización."""
    
    text: str = Field(
        ..., 
        max_length=50000, 
        description="Texto a resumir (máximo 50,000 caracteres)"
    )
    lang: str = Field(
        default="auto", 
        description="Idioma del texto (auto|es|en|fr|de|it|pt)"
    )
    max_tokens: int = Field(
        default=100, 
        ge=10, 
        le=1000, 
        description="Número máximo de tokens para el resumen (10-1000)"
    )
    tone: str = Field(
        default="neutral", 
        description="Tono del resumen (neutral|concise|bullet)"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Valida que el texto no esté vacío."""
        if not v or not v.strip():
            raise ValueError("El texto no puede estar vacío")
        return v.strip()
    
    @field_validator('lang')
    @classmethod
    def validate_lang(cls, v: str) -> str:
        """Valida que el idioma sea uno de los soportados."""
        supported_langs = ['auto', 'es', 'en', 'fr', 'de', 'it', 'pt']
        if v.lower() not in supported_langs:
            raise ValueError(f"Idioma no soportado. Idiomas válidos: {supported_langs}")
        return v.lower()
    
    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """Valida que el tono sea uno de los soportados."""
        supported_tones = ['neutral', 'concise', 'bullet']
        if v.lower() not in supported_tones:
            raise ValueError(f"Tono no soportado. Tonos válidos: {supported_tones}")
        return v.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Este es un texto de ejemplo que será resumido por el microservicio...",
                "lang": "es",
                "max_tokens": 150,
                "tone": "concise"
            }
        }
    }


class SummarizeResponse(BaseModel):
    """Response del endpoint de summarización."""
    
    summary: str = Field(
        ..., 
        description="Resumen generado del texto"
    )
    usage: Dict[str, int] = Field(
        ..., 
        description="Información de uso de tokens (prompt_tokens, completion_tokens)"
    )
    model: str = Field(
        ..., 
        description="Modelo utilizado para generar el resumen"
    )
    latency_ms: int = Field(
        ..., 
        description="Latencia de la operación en milisegundos"
    )
    fallback_used: bool = Field(
        default=False, 
        description="Indica si se usó el método de fallback"
    )
    cached: bool = Field(
        default=False,
        description="Indica si el resultado proviene del caché"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "summary": "Este es un resumen del texto proporcionado...",
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 40
                },
                "model": "gpt-5-nano",
                "latency_ms": 1250,
                "fallback_used": False,
                "cached": False
            }
        }
    }


class HealthResponse(BaseModel):
    """Response del endpoint de health check."""
    
    status: str = Field(
        ..., 
        description="Estado del servicio (ok|degraded|error)"
    )
    timestamp: str = Field(
        ..., 
        description="Timestamp de la verificación en formato ISO"
    )
    latency_ms: int = Field(
        ..., 
        description="Latencia de la verificación en milisegundos"
    )
    checks: Dict[str, str] = Field(
        ..., 
        description="Resultado de las verificaciones de salud"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "timestamp": "2024-01-15T10:30:00.000Z",
                "latency_ms": 45,
                "checks": {
                    "api": "ok",
                    "llm_provider": "ok"
                }
            }
        }
    }


class ErrorResponse(BaseModel):
    """Response estándar para errores."""
    
    error: str = Field(
        ..., 
        description="Tipo de error"
    )
    message: str = Field(
        ..., 
        description="Mensaje descriptivo del error"
    )
    request_id: Optional[str] = Field(
        default=None, 
        description="ID único del request que causó el error"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "El texto no puede estar vacío",
                "request_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    }
