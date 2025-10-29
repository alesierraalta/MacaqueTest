# Microservicio de Summarización con LLM

Un microservicio backend que recibe texto y devuelve resúmenes generados por OpenAI GPT-5 nano, priorizando **latencia** y **confiabilidad** con fallback automático.

## 🎯 Objetivo

Diseñar un microservicio backend que reciba texto y devuelva un resumen generado por un modelo de lenguaje (LLM), priorizando latencia y confiabilidad.

## 📋 Requisitos Funcionales

### POST /v1/summarize
**Request:**
```json
{
  "text": "string",
  "lang": "auto|es|en|...",
  "max_tokens": 100,
  "tone": "neutral|concise|bullet"
}
```

**Response:**
```json
{
  "summary": "string",
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 40
  },
  "model": "string",
  "latency_ms": 900,
  "fallback_used": false,
  "cached": false
}
```

### GET /v1/healthz
Revisión del estado del servicio y conectividad al LLM. Redis opcional.

**Auth:** API Key (`Authorization: Bearer <key>`)

## 🚀 Instalación y Configuración

### Paso 1: Clonar el Repositorio

```bash
git clone  https://github.com/alesierraalta/MacaqueTest.git
cd MacaqueTest
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar configuración
nano .env
```

**Configuración mínima requerida:**
```env
# API Keys permitidas (separadas por coma)
API_KEYS_ALLOWED=tu-api-key-123,otra-api-key-456

# API Key de OpenAI (REQUERIDA)
OPENAI_API_KEY=sk-tu-openai-api-key-aqui

# Modelo de OpenAI
OPENAI_MODEL=gpt-5-nano

# Configuración Redis (opcional)
ENABLE_REDIS=true
REDIS_URL=redis://redis:6379/0
CACHE_TTL_SECONDS=3600
RATE_LIMIT_REQUESTS=100
```

### Paso 3: Instalar Dependencias

```bash
# Instalar dependencias Python
pip install -r requirements.txt
```

### Paso 4: Ejecutar con Docker Compose (Recomendado)

```bash
# Construir y ejecutar servicios
docker-compose up --build

# En segundo plano
docker-compose up -d --build
```

### Paso 5: Verificar Instalación

```bash
# Health check
curl http://localhost:8000/v1/healthz

# Respuesta esperada:
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "latency_ms": 45,
  "checks": {
    "api": "ok",
    "llm_provider": "ok",
    "redis": "ok"
  }
}
```

## 📖 Uso de la API

### Documentación Interactiva

```bash
# Abrir documentación OpenAPI
open http://localhost:8000/docs
```

### Ejemplo 1: Resumen Básico

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Buenos días Alejandro, un placer saludarte. Te contacto para decir que hemos recibido tu CV y nos gustaría tener una charla para conocerte más en profundidad. ¿Nos puedes facilitar huecos que tengas disponibles? Quedamos a la espera.",
    "lang": "es",
    "max_tokens": 150,
    "tone": "concise"
  }'
```

**Respuesta esperada:**
```json
{
  "summary": "Empresa interesada en CV de Alejandro solicita entrevista para conocerlo mejor y pide disponibilidad horaria.",
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "model": "gpt-5-nano",
  "latency_ms": 1250,
  "fallback_used": false,
  "cached": false
}
```

### Ejemplo 2: Resumen con Tono Bullet

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "La empresa ABC ha reportado un aumento del 15% en sus ventas durante el último trimestre. Los productos más vendidos fueron smartphones y laptops. El CEO mencionó que planean expandirse a nuevos mercados en 2024.",
    "lang": "es",
    "max_tokens": 100,
    "tone": "bullet"
  }'
```

### Ejemplo 3: Resumen en Inglés

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quarterly earnings report shows significant growth in revenue. Our team has successfully launched three new products this quarter. Customer satisfaction ratings have improved by 20% compared to last quarter.",
    "lang": "en",
    "max_tokens": 80,
    "tone": "neutral"
  }'
```

### Ejemplo 4: Probar Caché de Redis

```bash
# Primera request (genera y cachea)
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Este es un texto de prueba para verificar el caché de Redis",
    "lang": "es",
    "max_tokens": 50,
    "tone": "concise"
  }'
```

**Respuesta esperada (primera request):**
```json
{
  "summary": "Texto de prueba para verificar el caché de Redis",
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "model": "gpt-5-nano",
  "latency_ms": 1250,
  "fallback_used": false,
  "cached": false
}
```

```bash
# Segunda request (mismo texto - usa caché)
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Este es un texto de prueba para verificar el caché de Redis",
    "lang": "es",
    "max_tokens": 50,
    "tone": "concise"
  }'
```

**Respuesta esperada (segunda request):**
```json
{
  "summary": "Texto de prueba para verificar el caché de Redis",
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "model": "gpt-5-nano",
  "latency_ms": 0,
  "fallback_used": false,
  "cached": true
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
                "text": "Texto a resumir aquí...",
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
            print(f"Cacheado: {data['cached']}")
        else:
            print(f"Error: {response.status_code}")

asyncio.run(summarize_text())
```

## ⚙️ Configuración Completa

### Variables de Entorno (12-factor)

| Variable | Descripción | Valor por Defecto | Requerido |
|----------|-------------|-------------------|-----------|
| `API_KEYS_ALLOWED` | API Keys permitidas (separadas por coma) | - | ✅ |
| `OPENAI_API_KEY` | API Key de OpenAI | - | ✅ |
| `OPENAI_MODEL` | Modelo de OpenAI | `gpt-5-nano` | ❌ |
| `SUMMARY_MAX_TOKENS` | Máximo tokens para resumen | `500` | ❌ |
| `LANG_DEFAULT` | Idioma por defecto | `auto` | ❌ |
| `REQUEST_TIMEOUT_MS` | Timeout del request | `10000` | ❌ |
| `LLM_TIMEOUT_MS` | Timeout de llamada LLM | `8000` | ❌ |
| `MAX_RETRIES` | Máximo número de reintentos | `2` | ❌ |
| `MAX_TEXT_LENGTH` | Longitud máxima del texto | `50000` | ❌ |
| `LOG_LEVEL` | Nivel de logging | `INFO` | ❌ |
| `ENABLE_REDIS` | Habilitar Redis | `true` | ❌ |
| `REDIS_URL` | URL de conexión Redis | `redis://redis:6379/0` | ❌ |
| `CACHE_TTL_SECONDS` | TTL del caché en segundos | `3600` | ❌ |
| `RATE_LIMIT_REQUESTS` | Requests por minuto por API key | `100` | ❌ |

### Tonos de Resumen Disponibles

- `neutral`: Tono neutral y objetivo
- `concise`: Tono conciso y directo  
- `bullet`: Formato de viñetas


## 🔧 Desarrollo Local

### Ejecutar sin Docker

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en modo desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar en modo producción
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
pytest tests/test_redis.py -v
pytest tests/test_fallback.py -v
```

## 🏗️ Arquitectura

```
Cliente → API (FastAPI) → LLM Provider
           ↳ Fallback: resumen extractivo
           ↳ Redis: caché + rate limiting
           ↳ Logs JSON estructurados
```

### Componentes

- **API**: Valida, autentica y llama al LLM
- **Proveedor LLM**: OpenAI GPT-5 nano configurable
- **Fallback**: TextRank si el modelo falla
- **Redis**: Caché y rate limiting (opcional)

## 🔒 Seguridad

### Autenticación Obligatoria

```bash
# Todos los endpoints requieren API Key
Authorization: Bearer tu-api-key-123
```

### Validaciones

- ✅ Texto ≤ 50k caracteres
- ✅ Idioma válido
- ✅ Entrada limpia
- ✅ API Key obligatoria
- ✅ Rate limit opcional (Redis)

### Logs Seguros

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.api.v1.endpoints.summarize",
  "message": "Request completado: /v1/summarize",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "endpoint": "/v1/summarize",
  "latency_ms": 1250,
  "model_used": "gpt-5-nano",
  "tokens_used": {"prompt_tokens": 0, "completion_tokens": 0},
  "fallback_used": false,
  "cached": false
}
```

## 🚀 Escalabilidad y Resiliencia

### Timeouts Configurados

- **Cliente**: 10s (`REQUEST_TIMEOUT_MS`)
- **LLM**: 8s (`LLM_TIMEOUT_MS`)

### Retries Automáticos

- Hasta 2 reintentos en errores 429/5xx
- Fallback extractivo ante fallas

### Redis (Opcional)

- **Caché**: Reduce latencia en textos repetidos
- **Rate Limiting**: 100 requests/minuto por API key
- **Graceful Degradation**: Servicio funciona si Redis falla

## 📊 Monitoreo

### Health Check

```bash
curl http://localhost:8000/v1/healthz
```

**Estados posibles:**
- `ok`: Todo funcionando
- `degraded`: LLM falló, fallback disponible
- `error`: Servicio no disponible

### Métricas Disponibles

- **Latencia**: Tiempo total de procesamiento
- **Modelo**: Modelo utilizado (gpt-5-nano o fallback)
- **Fallback Rate**: Uso del sistema de fallback
- **Cache Hit Rate**: Efectividad del caché
- **Error Rate**: Tasa de errores por endpoint

## 🐳 Despliegue

### Docker Compose (Recomendado)

```bash
# Construir y ejecutar
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Parar servicios
docker-compose down
```

### Docker Manual

```bash
# Construir imagen
docker build -t summarization-service .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env summarization-service
```

### Variables de Producción

```env
LOG_LEVEL=WARNING
REQUEST_TIMEOUT_MS=15000
LLM_TIMEOUT_MS=10000
ENABLE_REDIS=true
RATE_LIMIT_REQUESTS=200
```

## 📁 Estructura del Proyecto

```
MacaqueTest/
├── app/
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── api/v1/endpoints/
│   │   ├── summarize.py           # POST /v1/summarize
│   │   └── health.py              # GET /v1/healthz
│   ├── core/
│   │   ├── config.py              # Configuración 12-factor
│   │   ├── logging.py             # Logs JSON estructurados
│   │   ├── security.py            # Autenticación API Key
│   │   └── middleware.py          # Middleware personalizado
│   ├── models/requests.py          # Schemas Pydantic
│   └── services/
│       ├── llm_provider.py        # Integración OpenAI GPT-5
│       ├── fallback.py            # Resumen extractivo TextRank
│       └── redis_service.py       # Caché y rate limiting
├── tests/                         # Tests completos
├── docker-compose.yml            # Servicios Docker
├── Dockerfile                    # Imagen Docker
├── requirements.txt              # Dependencias Python
├── .env                          # Variables de entorno
├── .gitignore                    # Archivos ignorados
└── README.md                     # Este archivo
```

## ✅ Cumplimiento de Objetivos

### Latencia Optimizada
- ✅ Caché Redis reduce latencia a 0ms en textos repetidos
- ✅ Timeouts configurados (cliente 10s, LLM 8s)
- ✅ Fallback rápido con TextRank

### Confiabilidad Garantizada
- ✅ Fallback automático si LLM falla
- ✅ Retries en errores 429/5xx
- ✅ Graceful degradation si Redis falla
- ✅ Health check completo

### Escalabilidad
- ✅ Rate limiting por API key
- ✅ Caché distribuido con Redis
- ✅ Logs estructurados para monitoreo
- ✅ Configuración 12-factor

---

**Documentación OpenAPI**: http://localhost:8000/docs  
**Health Check**: http://localhost:8000/v1/healthz