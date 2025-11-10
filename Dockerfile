# Imagen base oficial de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivo de dependencias si existe (opcional)
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias básicas
RUN pip install --no-cache-dir fastapi uvicorn

# Copiar el código del proyecto
COPY ./FastApi/static ./static


# Exponer el puerto donde uvicorn servirá FastAPI
EXPOSE 8000

# Comando de ejecución
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
