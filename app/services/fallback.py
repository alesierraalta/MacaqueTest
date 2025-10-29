"""
Servicio de fallback usando TextRank para resumen extractivo.
Implementa resumen extractivo cuando falla el LLM principal.
"""

import nltk
from typing import Dict, Any, Optional
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExtractiveFallback:
    """Servicio de fallback usando TextRank."""
    
    def __init__(self):
        """Inicializa el servicio de fallback."""
        self._download_nltk_resources()
        self.summarizer = TextRankSummarizer()
        
    def _download_nltk_resources(self) -> None:
        """Descarga recursos necesarios de NLTK."""
        try:
            nltk.download('punkt', quiet=True)
            logger.info("Recursos NLTK descargados exitosamente")
        except Exception as e:
            logger.warning(f"Error descargando recursos NLTK: {e}")
    
    def _get_language_code(self, lang: str) -> str:
        """
        Convierte código de idioma a formato soportado por sumy.
        
        Args:
            lang: Código de idioma
            
        Returns:
            Código de idioma soportado por sumy
        """
        lang_map = {
            'es': 'spanish',
            'en': 'english', 
            'fr': 'french',
            'de': 'german',
            'it': 'italian',
            'pt': 'portuguese',
            'auto': 'spanish'  # Default a español
        }
        return lang_map.get(lang.lower(), 'spanish')
    
    def _calculate_sentence_count(self, text: str) -> int:
        """
        Calcula número óptimo de oraciones para el resumen.
        
        Args:
            text: Texto original
            
        Returns:
            Número de oraciones para el resumen
        """
        # Contar oraciones aproximadas
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        # Calcular número de oraciones para resumen (10-20% del original)
        if sentences <= 5:
            return max(1, sentences // 2)
        elif sentences <= 20:
            return max(2, sentences // 3)
        else:
            return max(3, sentences // 4)
    
    def generate_summary(
        self, 
        text: str, 
        lang: str = "auto", 
        max_sentences: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera resumen extractivo usando TextRank.
        
        Args:
            text: Texto original
            lang: Idioma del texto
            max_sentences: Máximo número de oraciones (opcional)
            
        Returns:
            Diccionario con summary y metadata
        """
        try:
            logger.info(
                f"Iniciando resumen extractivo con TextRank",
                extra={
                    'text_length': len(text),
                    'lang': lang,
                    'method': 'TextRank'
                }
            )
            
            # Determinar idioma
            language = self._get_language_code(lang)
            
            # Calcular número de oraciones si no se especifica
            if max_sentences is None:
                max_sentences = self._calculate_sentence_count(text)
            
            # Parsear texto
            parser = PlaintextParser.from_string(text, Tokenizer(language))
            
            # Generar resumen
            summary_sentences = self.summarizer(
                parser.document, 
                max_sentences
            )
            
            # Unir oraciones del resumen
            summary = ' '.join(str(sentence) for sentence in summary_sentences)
            
            # Si el resumen está vacío, usar primeras oraciones
            if not summary.strip():
                sentences = text.split('.')
                summary = '. '.join(sentences[:max_sentences]) + '.'
            
            logger.info(
                f"Resumen extractivo generado exitosamente",
                extra={
                    'summary_length': len(summary),
                    'sentences_used': len(summary_sentences),
                    'method': 'TextRank'
                }
            )
            
            return {
                "summary": summary,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "model": "TextRank-extractive",
                "method": "extractive",
                "sentences_used": len(summary_sentences)
            }
            
        except Exception as e:
            logger.error(
                f"Error en resumen extractivo: {e}",
                extra={'error_type': type(e).__name__}
            )
            
            # Fallback final: primeras oraciones del texto
            sentences = text.split('.')
            fallback_summary = '. '.join(sentences[:3]) + '.'
            
            return {
                "summary": fallback_summary,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "model": "fallback-simple",
                "method": "simple-extraction",
                "sentences_used": 3
            }


# Instancia global del servicio de fallback
extractive_fallback = ExtractiveFallback()
