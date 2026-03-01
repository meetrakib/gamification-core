# Dev Dockerfile: use with volume mount for hot reload (no COPY of app).
FROM python:3.12-slim

WORKDIR /app

# Install deps only (app code mounted at run time in dev)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Default: run uvicorn with reload when used via docker-compose (volume mount)
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
