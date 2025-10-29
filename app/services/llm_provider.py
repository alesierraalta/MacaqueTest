"""
Proveedor LLM usando OpenAI.
Implementa integración con OpenAI API con retries y manejo de errores.
"""

import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai._exceptions import RateLimitError, APIError, APITimeoutError
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider:
    """Proveedor LLM usando OpenAI API."""
    
    def __init__(self):
        """Inicializa el cliente OpenAI."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.llm_timeout_ms / 1000  # Convertir a segundos
        )
        self.model = settings.openai_model
        
    def _build_system_prompt(self, lang: str, tone: str) -> str:
        """
        Construye el prompt del sistema según el idioma y tono.
        
        Args:
            lang: Idioma del texto
            tone: Tono del resumen
            
        Returns:
            Prompt del sistema
        """
        # Mapeo de idiomas
        lang_map = {
            'es': 'español',
            'en': 'inglés',
            'fr': 'francés',
            'de': 'alemán',
            'it': 'italiano',
            'pt': 'portugués',
            'auto': 'el idioma detectado'
        }
        
        language = lang_map.get(lang, 'español')
        
        # Mapeo de tonos
        tone_map = {
            'neutral': 'un tono neutral y objetivo',
            'concise': 'un tono conciso y directo',
            'bullet': 'un formato de viñetas (bullet points)'
        }
        
        tone_desc = tone_map.get(tone, 'un tono neutral')
        
        return f"""Eres un asistente especializado en crear resúmenes de texto en {language}.

Instrucciones:
- Crea un resumen claro y preciso del texto proporcionado
- Mantén {tone_desc}
- Conserva la información más importante y relevante
- El resumen debe ser coherente y bien estructurado
- Si el texto está en {language}, responde en {language}

Responde únicamente con el resumen, sin explicaciones adicionales."""

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((RateLimitError, APIError)),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True
    )
    async def generate_summary(
        self, 
        text: str, 
        lang: str = "auto", 
        max_tokens: int = 100, 
        tone: str = "neutral"
    ) -> Dict[str, Any]:
        """
        Genera un resumen usando OpenAI API.
        
        Args:
            text: Texto a resumir
            lang: Idioma del texto
            max_tokens: Máximo número de tokens para el resumen
            tone: Tono del resumen
            
        Returns:
            Diccionario con summary, usage, model
            
        Raises:
            RateLimitError: Si se excede el límite de rate
            APIError: Si hay error en la API
            Timeout: Si se excede el timeout
        """
        try:
            # Construir mensajes
            system_prompt = self._build_system_prompt(lang, tone)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            logger.info(
                f"Iniciando llamada a OpenAI con modelo {self.model}",
                extra={
                    'model': self.model,
                    'text_length': len(text),
                    'max_tokens': max_tokens,
                    'lang': lang,
                    'tone': tone
                }
            )
            
            # Llamar a OpenAI API usando responses.create con instructions
            response = await self.client.responses.create(
                model=self.model,
                instructions=system_prompt,  # Agregar system prompt como instructions
                input=text
            )
            
            # Extraer información de la respuesta
            summary = response.output_text or ""
            
            # Intentar obtener tokens de uso de la respuesta
            # Si no están disponibles, mantener en 0 (prioridad: latencia)
            usage = {
                "prompt_tokens": getattr(response, 'prompt_tokens', 0),
                "completion_tokens": getattr(response, 'completion_tokens', 0),
                "total_tokens": getattr(response, 'total_tokens', 0)
            }
            
            # Validar que la respuesta tenga contenido válido
            if not summary or len(summary.strip()) < 10:
                raise APIError("Respuesta vacía o inválida del LLM")
            
            logger.info(
                f"Resumen generado exitosamente con OpenAI",
                extra={
                    'model': self.model,
                    'tokens_used': usage,
                    'summary_length': len(summary)
                }
            )
            
            return {
                "summary": summary,
                "usage": usage,
                "model": self.model
            }
            
        except RateLimitError as e:
            logger.warning(
                f"Rate limit excedido en OpenAI: {e}",
                extra={'error_type': 'RateLimitError'}
            )
            raise
            
        except APIError as e:
            logger.error(
                f"Error de API en OpenAI: {e}",
                extra={'error_type': 'APIError', 'status_code': getattr(e, 'status_code', None)}
            )
            raise
            
        except APITimeoutError as e:
            logger.error(
                f"Timeout en llamada a OpenAI: {e}",
                extra={'error_type': 'Timeout'}
            )
            raise
            
        except Exception as e:
            logger.error(
                f"Error inesperado en OpenAI: {e}",
                extra={'error_type': type(e).__name__}
            )
            raise APIError(f"Error inesperado: {e}")

    async def test_connection(self) -> bool:
        """
        Prueba la conectividad con OpenAI API.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Llamada simple para probar conectividad usando responses.create
            response = await self.client.responses.create(
                model=self.model,
                instructions="You are a helpful assistant.",  # Agregar instructions
                input="test"
            )
            return True
            
        except Exception as e:
            logger.warning(
                f"Error en test de conectividad OpenAI: {e}",
                extra={'error_type': type(e).__name__}
            )
            return False


# Instancia global del proveedor
openai_provider = OpenAIProvider()
