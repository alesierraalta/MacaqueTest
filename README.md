# Microservicio de Summarización con LLM

Un microservicio backend que recibe texto y devuelve resúmenes generados por OpenAI GPT-5 nano, con fallback automático para garantizar disponibilidad.

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
cp .env.example .env
```

Editar `.env`:
```env
API_KEYS_ALLOWED=tu-api-key-123,otra-api-key-456
OPENAI_API_KEY=sk-tu-openai-api-key-aqui
OPENAI_MODEL=gpt-5-nano
```

### 2. Ejecutar con Docker

```bash
docker-compose up --build
```

### 3. Verificar Funcionamiento

```bash
# Health check
curl http://localhost:8000/v1/healthz

# Documentación interactiva
open http://localhost:8000/docs
```

## 📖 Uso de la API

### Autenticación

Todos los endpoints requieren API Key:
```bash
Authorization: Bearer tu-api-key-123
```

### Generar Resumen

```bash
curl -X POST "http://localhost:8000/v1/summarize" \
  -H "Authorization: Bearer tu-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Este es un texto largo que será resumido...",
    "lang": "es",
    "max_tokens": 150,
    "tone": "concise"
  }'
```

**Respuesta:**
```json
{
  "summary": "Resumen generado del texto...",
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
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

**Respuesta:**
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

asyncio.run(summarize_text())
```

## ⚙️ Configuración

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


### Tonos de Resumen

- `neutral`: Tono neutral y objetivo
- `concise`: Tono conciso y directo
- `bullet`: Formato de viñetas

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

## 📊 Monitoreo

### Logs Estructurados JSON

El servicio genera logs JSON con:
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
  "fallback_used": false
}
```

### Métricas Disponibles

- **Latencia**: Tiempo total de procesamiento
- **Modelo**: Modelo utilizado (gpt-5-nano o fallback)
- **Fallback Rate**: Uso del sistema de fallback
- **Error Rate**: Tasa de errores por endpoint

## 🏗️ Estructura del Proyecto

```
MacaqueTest/
├── app/
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── api/v1/endpoints/
│   │   ├── summarize.py           # POST /v1/summarize
│   │   └── health.py              # GET /v1/healthz
│   ├── core/
│   │   ├── config.py              # Configuración
│   │   ├── logging.py             # Logs estructurados
│   │   ├── security.py            # Autenticación API Key
│   │   └── middleware.py          # Middleware personalizado
│   ├── models/requests.py         # Schemas Pydantic
│   └── services/
│       ├── llm_provider.py        # Integración OpenAI
│       └── fallback.py            # Resumen extractivo TextRank
├── tests/                         # Tests
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
LOG_LEVEL=WARNING
CORS_ORIGINS=https://tu-dominio.com
REQUEST_TIMEOUT_MS=15000
LLM_TIMEOUT_MS=10000
```

- **Documentación**: `/docs` en el servidor
- **Logs**: `docker-compose logs -f`
- **Health Check**: `http://localhost:8000/v1/healthz`