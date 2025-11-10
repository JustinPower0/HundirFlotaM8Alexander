# Dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y curl

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la app
COPY FastApi/ ./FastApi/
COPY Programa/ ./Programa/
COPY data/ ./data/

# Exponer el puerto
EXPOSE 8000

# Ejecutar FastAPI con uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
