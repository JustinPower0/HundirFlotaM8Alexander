FROM python:3.11-slim

WORKDIR /app

# Copiar el backend
COPY FastApi/ ./FastApi

# Copiar e instalar dependencias
COPY FastApi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "FastApi.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
