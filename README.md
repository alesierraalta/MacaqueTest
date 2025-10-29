# Microservicio de Summarización con LLM

Un microservicio backend robusto y escalable que recibe texto y devuelve resúmenes generados por OpenAI GPT-5 nano, priorizando latencia y confiabilidad.

## 🎯 Objetivo

Diseñar un microservicio que genere resúmenes de texto usando OpenAI GPT-5 nano como proveedor principal, con un sistema de fallback extractivo usando TextRank para garantizar disponibilidad del servicio.

## 🏗️ Arquitectura

```
Cliente → API (FastAPI) → OpenAI Provider
           ↳ Fallback: TextRank Extractivo
           ↳ Logs JSON Estructurados
           ↳ Autenticación API Key
```

### Componentes Principales

- **API FastAPI**: Valida, autentica y procesa requests
- **Proveedor LLM**: Integración con OpenAI GPT-5 nano
- **Fallback Extractivo**: TextRank usando sumy para garantizar respuesta
- **Sistema de Logs**: Logs JSON estructurados para monitoreo
- **Autenticación**: API Key obligatoria para todos los endpoints

## 🚀 Características

### ✅ Implementado (Fase Inicial)

- **Endpoint POST /v1/summarize**: Genera resúmenes con validación completa
- **Endpoint GET /v1/healthz**: Health check con verificación de conectividad
- **Autenticación API Key**: Sistema de seguridad con HTTPBearer
- **Logs JSON Estructurados**: Logging completo con request_id y métricas
- **Fallback Automático**: TextRank cuando OpenAI falla
- **Retries Inteligentes**: Exponential backoff para errores 429/5xx
- **Docker Compose**: Despliegue containerizado
- **Tests Comprehensivos**: Cobertura completa con pytest
- **Documentación OpenAPI**: Interfaz interactiva en /docs

### 🔄 Resiliencia y Confiabilidad

- **Timeouts Configurados**: Cliente 10s, LLM 8s
- **Retries Automáticos**: Máximo 2 reintentos con exponential backoff
- **Fallback Garantizado**: TextRank asegura respuesta siempre
- **Health Check**: Monitoreo continuo del estado del servicio
- **Manejo Granular de Errores**: Logs detallados sin datos sensibles

## 📋 Requisitos Previos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- API Key de OpenAI válida

## 🛠️ Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd MacaqueTest
```

### 2. Configurar Variables de Entorno

```bash
cp .env.example .env
```

Editar `.env` con tus valores:

```env
# API Keys permitidas (separadas por coma)
API_KEYS_ALLOWED=tu-api-key-123,otra-api-key-456

# Configuración OpenAI
OPENAI_API_KEY=sk-tu-openai-api-key-aqui
OPENAI_MODEL=gpt-5-nano

# Configuración opcional
SUMMARY_MAX_TOKENS=500
LANG_DEFAULT=auto
LOG_LEVEL=INFO
```

### 3. Ejecutar con Docker Compose

```bash
# Construir y ejecutar
docker-compose up --build

# En modo detached
docker-compose up -d --build
```

### 4. Verificar Instalación

```bash
# Health check
curl http://localhost:8000/v1/healthz

# Documentación interactiva
open http://localhost:8000/docs
```

## 🔧 Desarrollo Local

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Ejecutar Servicio

```bash
# Modo desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Modo producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests con cobertura
pytest --cov=app

# Tests específicos
pytest tests/test_summarize.py -v
```

## 📖 Uso de la API

### Autenticación

Todos los endpoints requieren autenticación con API Key:

```bash
Authorization: Bearer tu-api-key-123
```

### Generar Resumen

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Este es un texto largo que será resumido por el microservicio...",
    "lang": "es",
    "max_tokens": 150,
    "tone": "concise"
  }'
```

**Response:**
```json
{
  "summary": "Resumen generado del texto...",
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 40,
    "total_tokens": 160
  },
  "model": "gpt-5-nano",
  "latency_ms": 1250,
  "fallback_used": false
}
```

### Health Check

```bash
curl http://localhost:8000/v1/healthz
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "latency_ms": 45,
  "checks": {
    "api": "ok",
    "llm_provider": "ok"
  }
}
```

## 🐍 Ejemplo con Python

```python
import httpx
import asyncio

async def summarize_text():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/summarize",
            headers={"Authorization": "Bearer tu-api-key-123"},
            json={
                "text": "Texto a resumir...",
                "lang": "es",
                "max_tokens": 100,
                "tone": "neutral"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Resumen: {data['summary']}")
            print(f"Modelo: {data['model']}")
            print(f"Latencia: {data['latency_ms']}ms")
        else:
            print(f"Error: {response.status_code}")

# Ejecutar
asyncio.run(summarize_text())
```

## ⚙️ Configuración Avanzada

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `API_KEYS_ALLOWED` | API Keys permitidas (separadas por coma) | **Requerido** |
| `OPENAI_API_KEY` | API Key de OpenAI | **Requerido** |
| `OPENAI_MODEL` | Modelo de OpenAI | `gpt-5-nano` |
| `SUMMARY_MAX_TOKENS` | Máximo tokens para resumen | `500` |
| `LANG_DEFAULT` | Idioma por defecto | `auto` |
| `REQUEST_TIMEOUT_MS` | Timeout del request | `10000` |
| `LLM_TIMEOUT_MS` | Timeout de llamada LLM | `8000` |
| `MAX_RETRIES` | Máximo número de reintentos | `2` |
| `MAX_TEXT_LENGTH` | Longitud máxima del texto | `50000` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |

### Idiomas Soportados

- `auto`: Detección automática
- `es`: Español
- `en`: Inglés
- `fr`: Francés
- `de`: Alemán
- `it`: Italiano
- `pt`: Portugués

### Tonos de Resumen

- `neutral`: Tono neutral y objetivo
- `concise`: Tono conciso y directo
- `bullet`: Formato de viñetas

## 📊 Monitoreo y Logs

### Logs Estructurados JSON

El servicio genera logs JSON estructurados con:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.api.v1.endpoints.summarize",
  "message": "Request completado: /v1/summarize",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "endpoint": "/v1/summarize",
  "latency_ms": 1250,
  "model_used": "gpt-4o-mini",
  "tokens_used": {"prompt_tokens": 120, "completion_tokens": 40},
  "fallback_used": false
}
```

### Métricas de Rendimiento

- **Latencia**: Tiempo total de procesamiento
- **Tokens**: Uso de tokens de OpenAI
- **Fallback Rate**: Porcentaje de uso del fallback
- **Error Rate**: Tasa de errores por endpoint

## 🧪 Testing

### Estructura de Tests

```
tests/
├── conftest.py          # Configuración y fixtures
├── test_auth.py         # Tests de autenticación
├── test_summarize.py    # Tests del endpoint principal
├── test_health.py        # Tests de health check
└── test_fallback.py     # Tests del servicio de fallback
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_summarize.py -v

# Tests con cobertura
pytest --cov=app --cov-report=html

# Tests en paralelo
pytest -n auto
```

## 🏗️ Estructura del Proyecto

```
MacaqueTest/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── api/
│   │   ├── v1/
│   │   │   └── endpoints/
│   │   │       ├── summarize.py   # POST /v1/summarize
│   │   │       └── health.py      # GET /v1/healthz
│   ├── core/
│   │   ├── config.py              # Configuración (12-factor)
│   │   ├── logging.py             # Logs estructurados JSON
│   │   ├── security.py            # Autenticación API Key
│   │   └── middleware.py          # Middleware personalizado
│   ├── models/
│   │   └── requests.py            # Schemas Pydantic
│   └── services/
│       ├── llm_provider.py        # Integración OpenAI
│       └── fallback.py            # Resumen extractivo TextRank
├── tests/                         # Tests comprehensivos
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 🔒 Seguridad

- **API Key Obligatoria**: Todos los endpoints requieren autenticación
- **Validación Estricta**: Validación completa de entrada
- **Logs Seguros**: No se loguean datos sensibles
- **Headers de Seguridad**: CORS, XSS protection, etc.
- **Límites de Payload**: Máximo 50k caracteres de texto

## 🚀 Despliegue

### Docker Compose (Recomendado)

```bash
docker-compose up -d --build
```

### Docker Manual

```bash
# Construir imagen
docker build -t summarization-service .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env summarization-service
```

### Variables de Entorno de Producción

```env
# Producción
LOG_LEVEL=WARNING
CORS_ORIGINS=https://tu-dominio.com
REQUEST_TIMEOUT_MS=15000
LLM_TIMEOUT_MS=10000
```

## 📈 Roadmap (Futuro)

### Fase 2 - Características Opcionales

- [ ] **Redis Integration**: Caché y rate limiting
- [ ] **Evaluador de Calidad**: Métricas automáticas de resúmenes
- [ ] **Múltiples Proveedores**: Soporte para Anthropic, Cohere, etc.
- [ ] **Métricas Avanzadas**: Prometheus/Grafana
- [ ] **Rate Limiting**: Límites por API key
- [ ] **Batch Processing**: Procesamiento en lote

### Fase 3 - Escalabilidad

- [ ] **Load Balancing**: Múltiples instancias
- [ ] **Database Integration**: Persistencia de métricas
- [ ] **Queue System**: Procesamiento asíncrono
- [ ] **Monitoring**: Alertas y dashboards

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

- **Documentación**: `/docs` en el servidor
- **Issues**: GitHub Issues
- **Logs**: Verificar logs del contenedor con `docker-compose logs -f`

---

**Desarrollado con ❤️ usando FastAPI, OpenAI y Python**
