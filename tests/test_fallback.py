"""
Tests para el servicio de fallback extractivo.
Verifica el funcionamiento del fallback con TextRank.
"""

import pytest
from unittest.mock import patch
from app.services.fallback import ExtractiveFallback


class TestExtractiveFallback:
    """Tests para el servicio de fallback extractivo."""
    
    def test_fallback_initialization(self):
        """Test de inicialización del servicio de fallback."""
        fallback = ExtractiveFallback()
        assert fallback.summarizer is not None
    
    def test_generate_summary_success(self, sample_text):
        """Test de generación exitosa de resumen."""
        fallback = ExtractiveFallback()
        
        result = fallback.generate_summary(
            text=sample_text,
            lang="es",
            max_sentences=2
        )
        
        assert "summary" in result
        assert "usage" in result
        assert "model" in result
        assert "method" in result
        assert "sentences_used" in result
        
        assert result["model"] == "TextRank-extractive"
        assert result["method"] == "extractive"
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0
    
    def test_generate_summary_different_languages(self, sample_text):
        """Test con diferentes idiomas."""
        fallback = ExtractiveFallback()
        
        languages = ["es", "en", "fr", "de", "it", "pt", "auto"]
        
        for lang in languages:
            result = fallback.generate_summary(
                text=sample_text,
                lang=lang
            )
            
            assert "summary" in result
            assert len(result["summary"]) > 0
    
    def test_generate_summary_empty_text(self):
        """Test con texto vacío."""
        fallback = ExtractiveFallback()
        
        result = fallback.generate_summary(
            text="",
            lang="es"
        )
        
        # Debería manejar texto vacío graciosamente
        assert "summary" in result
        assert isinstance(result["summary"], str)
    
    def test_generate_summary_short_text(self):
        """Test con texto muy corto."""
        fallback = ExtractiveFallback()
        
        short_text = "Texto corto."
        
        result = fallback.generate_summary(
            text=short_text,
            lang="es"
        )
        
        assert "summary" in result
        assert len(result["summary"]) > 0
    
    def test_calculate_sentence_count(self):
        """Test de cálculo de número de oraciones."""
        fallback = ExtractiveFallback()
        
        # Texto con pocas oraciones
        short_text = "Primera oración. Segunda oración."
        count = fallback._calculate_sentence_count(short_text)
        assert count >= 1
        
        # Texto con muchas oraciones
        long_text = ". ".join([f"Oración {i}" for i in range(50)]) + "."
        count = fallback._calculate_sentence_count(long_text)
        assert count >= 3
    
    def test_get_language_code(self):
        """Test de conversión de códigos de idioma."""
        fallback = ExtractiveFallback()
        
        test_cases = [
            ("es", "spanish"),
            ("en", "english"),
            ("fr", "french"),
            ("de", "german"),
            ("it", "italian"),
            ("pt", "portuguese"),
            ("auto", "spanish"),
            ("invalid", "spanish")
        ]
        
        for input_lang, expected in test_cases:
            result = fallback._get_language_code(input_lang)
            assert result == expected
    
    def test_fallback_with_error(self):
        """Test de fallback cuando hay error en TextRank."""
        fallback = ExtractiveFallback()
        
        # Mock para simular error en TextRank
        with patch.object(fallback.summarizer, '__call__', side_effect=Exception("TextRank error")):
            result = fallback.generate_summary(
                text="Texto de prueba con múltiples oraciones. Segunda oración. Tercera oración.",
                lang="es"
            )
            
            # Debería usar fallback simple
            assert "summary" in result
            assert result["model"] == "fallback-simple"
            assert result["method"] == "simple-extraction"
            assert len(result["summary"]) > 0


class TestFallbackIntegration:
    """Tests de integración del fallback."""
    
    def test_fallback_usage_in_summarize(self, client, sample_request, valid_api_key):
        """Test de uso del fallback en el endpoint de summarización."""
        with patch('app.services.llm_provider.openai_provider.generate_summary') as mock_generate:
            # Simular error en OpenAI
            mock_generate.side_effect = Exception("OpenAI error")
            
            headers = {"Authorization": f"Bearer {valid_api_key}"}
            response = client.post("/v1/summarize", json=sample_request, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["fallback_used"] is True
            assert "TextRank" in data["model"]
            assert len(data["summary"]) > 0
