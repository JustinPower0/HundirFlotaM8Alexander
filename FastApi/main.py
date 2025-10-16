from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import uuid
import json

# Variable
partida = {}
matriz = []
barcos_definicion = {
    "submari": {"id": 1, "longitud": 1},
    "destructor": {"id": 2, "longitud": 2},
    "creuer": {"id": 3, "longitud": 3},
    "cuirassat": {"id": 4, "longitud": 4},
    "portaavions": {"id": 5, "longitud": 5}
}


# Funciones Normales

# Funcion Crear Matriz
def crearMatriz(filas,columnas):
    matriz = []
    for i in range(filas):
        fila = []
        for j in range(columnas):
            fila.append(0)
        matriz.append(fila)
    return matriz

# Funcion Agrergar Matriz Partida
def agregarMatrizPartida(partida, filas, columnas,nombre_usuario):
    matriz = crearMatriz(filas,columnas)
    partida_id = str(uuid.uuid4())
    partida[partida_id] = matriz
    partida[nombre_usuario] = nombre_usuario
    return partida_id, matriz,nombre_usuario

# Funcion Agregar Barcos
def agregarbarcos(partida, partida_id):
    matriz = partida.get(partida_id)
    if matriz is None:
        return {"error": "Partida no encontrada"}

    filas = len(matriz)
    columnas = len(matriz[0])
    total_casillas = filas * columnas
    limite_ocupacion = int(total_casillas * 0.3)

    barcos = {}
    estado = {"ocupadas": 0}
    id_por_tipo = {nombre: 1 for nombre in barcos_definicion}

    def colocar_barco(nombre, info):
        tipo = info["id"]
        longitud = info["longitud"]
        intentos = 0
        continuar = False

        while intentos < 100:
            orientacion = random.choice(["horizontal", "vertical"])
            if orientacion == "horizontal":
                fila = random.randint(0, filas - 1)
                col = random.randint(0, columnas - longitud)
                posiciones = [(fila, col + i) for i in range(longitud)]
            else:
                fila = random.randint(0, filas - longitud)
                col = random.randint(0, columnas - 1)
                posiciones = [(fila + i, col) for i in range(longitud)]

            libre = True
            for x, y in posiciones:
                if matriz[x][y] != 0:
                    libre = False
                    break

            if libre:
                for x, y in posiciones:
                    matriz[x][y] = tipo
                if nombre not in barcos:
                    barcos[nombre] = []
                barcos[nombre].append({
                    "id": id_por_tipo[nombre],
                    "posiciones": posiciones
                })
                id_por_tipo[nombre] += 1
                estado["ocupadas"] += longitud
                continuar = True
                break
            intentos += 1
        return continuar

    for nombre, info in barcos_definicion.items():
        colocado = colocar_barco(nombre, info)
        if not colocado:
            return {"error": f"No se pudo colocar el barco {nombre}"}

    while estado["ocupadas"] < limite_ocupacion:
        nombre, info = random.choice(list(barcos_definicion.items()))
        if estado["ocupadas"] + info["longitud"] > limite_ocupacion:
            break
        colocar_barco(nombre, info)

    return {"matriz": matriz, "barcos": barcos}

# Crear la aplicación
app = FastAPI(title="Mi Projecto", version="0.0.1")

# Lista de orígenes permitidos
origins = [
    "http://localhost:5500",  # si tu frontend corre aquí
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
     #allow_origins=["*"],  # permite cualquier origen (no recomendable en producción)
    allow_origins=origins,  # permite solo esos orígenes
    allow_credentials=True,
    allow_methods=["*"],    # permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],    # permite todas las cabeceras
)

# Funciones FastApi
@app.get("/partida/{filas}/{columnas}/{nombre_usuario}", tags=["Partida"])
def devolver_matriz(filas: int,columnas: int,nombre_usuario:str):
    global partida
    partida_id, matriz,nombre_usuario = agregarMatrizPartida(partida, filas,columnas,nombre_usuario)
    return {"id": partida_id,"nom": nombre_usuario, "matriz": matriz}

@app.get("/barcos/{partida_id}", tags=["Barcos"])
def colocar_barcos(partida_id: str):
    resultado = agregarbarcos(partida, partida_id)
    return resultado

@app.get("/estadisticas", tags=["Estadisticas"])                     #funcion get para tener las estadisticas
def leerEstadisticas():
    with open("../data/stats.json", "r") as archivo:
        datos = json.load(archivo)
        return datos
