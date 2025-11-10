# Imagen base oficial de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el contenido del proyecto
COPY ./FastApi ./FastApi
COPY ./Programa ./Programa

# Instalar dependencias
RUN pip install fastapi uvicorn

# Exponer el puerto 8000
EXPOSE 8000

# Ir al directorio FastApi y lanzar el servidor igual que haces localmente
WORKDIR /app/FastApi

# Comando de ejecución (sin reload porque Docker ya hace el hot-reload en dev)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
