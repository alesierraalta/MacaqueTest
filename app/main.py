"""
Aplicación principal FastAPI del microservicio de summarización.
Configura la aplicación con todos los componentes necesarios.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, get_logger, log_error
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.api.v1.endpoints import summarize, health
from app.models.requests import ErrorResponse

# Configurar logging
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # Startup
    logger.info("Iniciando microservicio de summarización")
    logger.info(f"Configuración: modelo={settings.openai_model}, timeout={settings.llm_timeout_ms}ms")
    
    yield
    
    # Shutdown
    logger.info("Cerrando microservicio de summarización")


# Crear aplicación FastAPI
app = FastAPI(
    title="Microservicio de Summarización LLM",
    description="Servicio para generar resúmenes de texto usando OpenAI con fallback extractivo",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Agregar middlewares personalizados
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Incluir routers
app.include_router(
    health.router,
    prefix="/v1",
    tags=["health"]
)

app.include_router(
    summarize.router,
    prefix="/v1",
    tags=["summarization"]
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Maneja excepciones HTTP."""
    request_id = getattr(request.state, 'request_id', None)
    
    log_error(
        logger=logger,
        request_id=request_id,
        error=exc,
        endpoint=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            request_id=request_id
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Maneja excepciones generales."""
    request_id = getattr(request.state, 'request_id', None)
    
    log_error(
        logger=logger,
        request_id=request_id,
        error=exc,
        endpoint=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="Error interno del servidor",
            request_id=request_id
        ).model_dump()
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz con información del servicio."""
    return {
        "service": "Microservicio de Summarización LLM",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "health": "/v1/healthz"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
