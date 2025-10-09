from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Funciones Normales

def crearMatriz(dim):
    matriz = []
    for i in range(dim):
        fila = []
        for j in range(dim):
            fila.append(0)
        matriz.append(fila)
    return matriz


# Variable
partida = {}
barco1 = [1]
barco2 = [2,2]
barco3 = [3,3,3]
barco4 = [4,4,4,4]
barco5 = [5,5,5,5,5]
dimencion = 7
matriz = crearMatriz(dimencion)

# Crear la aplicación
app = FastAPI(title="Mi Projecto", version="0.0.1")

# Lista de orígenes permitidos
origins = [
    "http://localhost:5500",  # si tu frontend corre aquí
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],  # permite cualquier origen (no recomendable en producción)
    allow_origins=origins,  # permite solo esos orígenes
    allow_credentials=True,
    allow_methods=["*"],    # permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],    # permite todas las cabeceras
)

# Funciones FastApi
@app.get("/matriz")
def read_root():
    return matriz

@app.get("/saludo/{nombre}")
def read_item(nombre: str):
    return {"saludo": f"Hola {nombre}!"}
