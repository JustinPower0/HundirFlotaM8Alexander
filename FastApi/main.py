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

def agregarMatrizPartida(partida, dim, contador):
    matriz = crearMatriz(dim)
    partida[contador] = matriz
    return contador + 1, matriz

# Variable
partida = {}
matriz = []
contador = 1
barco1 = [1]
barco2 = [2,2]
barco3 = [3,3,3]
barco4 = [4,4,4,4]
barco5 = [5,5,5,5,5]

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
@app.get("/partida/{dim}", tags=["Partida"])
def devolver_matriz(dim: int):
    global partida,contador
    if dim < 7 or dim > 20:
        return {"error": "Dimensión inválida, debe estar entre 7 y 20"}
    contador, matriz = agregarMatrizPartida(partida, dim, contador)
    return {"id": contador - 1, "matriz": matriz}
