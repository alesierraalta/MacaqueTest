# Stage 1: Builder - Construir dependencias Python
FROM python:3.11-slim as builder

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements y instalar dependencias Python en directorio de usuario
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Imagen final optimizada
FROM python:3.11-slim

# Instalar dependencias mínimas del sistema (solo curl para health check)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copiar dependencias instaladas desde builder al directorio del usuario app
COPY --from=builder /root/.local /home/app/.local

# Copiar código de la aplicación
COPY ./app ./app

# Cambiar ownership de los archivos al usuario app
RUN chown -R app:app /app /home/app/.local

# Cambiar al usuario app (principio de menor privilegio)
USER app

# Configurar PATH para usar dependencias instaladas
ENV PATH=/home/app/.local/bin:$PATH

# Exponer puerto 8000 para la aplicación
EXPOSE 8000

# Health check para verificar que la aplicación esté funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/healthz || exit 1

# Comando por defecto para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
