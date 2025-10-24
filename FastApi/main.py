from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import uuid
import json
import os
from datetime import datetime

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
    partida[partida_id] = {
        "matriz": matriz,
        "jugador": nombre_usuario,
        "barcos": {}
    }
    return partida_id, matriz,nombre_usuario

# Funcion Agregar Barcos
def agregarbarcos(partida, partida_id):
    datos = partida.get(partida_id)
    if datos is None:
        return {"error": "Partida no encontrada"}
    
    matriz = datos["matriz"]
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
    datos["barcos"] = barcos
    return {"matriz": matriz, "barcos": barcos}

def actualizar_stats(jugador, puntuacio, files, columnes, duracio_ms):
    ruta = "../data/stats.json"

    # Estructura base si el archivo no existe
    stats = {
        "total_partides": 0,
        "millor_puntuacio": 0,
        "millor_jugador": "",
        "data_millor": "",
        "rànquing_top5": []
    }

    # Leer archivo si existe
    if os.path.exists(ruta):
        with open(ruta, "r") as archivo:
            stats = json.load(archivo)

    # Actualizar total de partidas
    stats["total_partides"] += 1

    # Actualizar mejor puntuación
    if puntuacio > stats["millor_puntuacio"]:
        stats["millor_puntuacio"] = puntuacio
        stats["millor_jugador"] = jugador
        stats["data_millor"] = datetime.now().isoformat()

    # Añadir al rànquing_top5 si aplica
    nueva_entrada = {
        "jugador": jugador,
        "puntuacio": puntuacio,
        "files": files,
        "columnes": columnes,
        "data": datetime.now().isoformat(),
        "duracio_ms": duracio_ms
    }

    stats["rànquing_top5"].append(nueva_entrada)
    stats["rànquing_top5"] = sorted(stats["rànquing_top5"], key=lambda x: x["puntuacio"], reverse=True)[:5]

    # Guardar archivo
    with open(ruta, "w") as archivo:
        json.dump(stats, archivo, indent=2)

def calcular_puntuacio(dispars, encerts, vaixells_enfonsats, temps_inici, temps_final, estat):
    BASE = 1000
    COST_DISPAR = -10
    BONUS_ENCERT = 20
    BONUS_ENFONSAT = 50
    PENAL_TEMPS = -1

    if estat == "abandonada":
        return 0

    duracio = (temps_final - temps_inici).total_seconds()
    puntuacio = (
        BASE +
        dispars * COST_DISPAR +
        encerts * BONUS_ENCERT +
        vaixells_enfonsats * BONUS_ENFONSAT +
        int(duracio) * PENAL_TEMPS
    )

    return max(puntuacio, 0)

async def guardar_temporal_partida(partida_id):
    datos = partida.get(partida_id)
    if datos is None:
        return

    matriz = datos["matriz"]
    barcos = datos["barcos"]
    disparos = datos.get("traza", [])
    jugador = datos.get("jugador", "anònim")
    estado = datos.get("estado", "en_curs")
    inicio = datos.get("inicio", datetime.now()).isoformat()
    fin = datetime.now().isoformat() if estado != "en_curs" else None

    # Construir lista de barcos
    barcos_json = []
    for tipo, lista in barcos.items():
        for barco in lista:
            posiciones = barco.get("posiciones_originales", barco["posiciones"])
            tocadas = sum(1 for disparo in disparos if disparo["coordenada"] in posiciones)
            barcos_json.append({
                "tipus": tipo,
                "mida": len(posiciones),
                "posicions": posiciones,
                "tocades": tocadas,
                "enfonsat": len(barco["posiciones"]) == 0
            })

    resumen = {
        "game_id": partida_id,
        "files": len(matriz),
        "columnes": len(matriz[0]),
        "tauler": matriz,
        "vaixells": barcos_json,
        "dispars": [
            {
                "fila": disparo["coordenada"][0],
                "col": disparo["coordenada"][1],
                "resultat": disparo["resultado"]
            } for disparo in disparos
        ],
        "vaixells_totals": sum(len(b) for b in barcos.values()),
        "vaixells_enfonsats": sum(1 for b in barcos_json if b["enfonsat"]),
        "caselles_destapades": len(datos.get("impactos", [])),
        "estat": estado,
        "jugador": jugador,
        "data_inici": inicio,
        "data_fi": fin
    }

    ruta = f"../data/games/{partida_id}.json"
    async with open(ruta, "w") as archivo:
         json.dump(resumen, archivo, indent=2)

def volcar_a_stats(partida_id):
    ruta_partida = f"../data/games/{partida_id}.json"
    ruta_stats = "../data/stats.json"

    if not os.path.exists(ruta_partida):
        return

    with open(ruta_partida, "r") as archivo:
        partida = json.load(archivo)

    puntuacio = partida.get("puntuacion", 0)
    jugador = partida.get("jugador", "anònim")
    files = partida.get("files", 0)
    columnes = partida.get("columnes", 0)
    data = partida.get("data_fi", datetime.now().isoformat())
    duracio_ms = partida.get("duracion_ms", 0)

    # Estructura base si no existe
    stats = {
        "total_partides": 0,
        "millor_puntuacio": 0,
        "millor_jugador": "",
        "data_millor": "",
        "rànquing_top5": []
    }

    if os.path.exists(ruta_stats):
        with open(ruta_stats, "r") as archivo:
            stats = json.load(archivo)

    stats["total_partides"] += 1

    if puntuacio > stats["millor_puntuacio"]:
        stats["millor_puntuacio"] = puntuacio
        stats["millor_jugador"] = jugador
        stats["data_millor"] = data

    entrada = {
        "jugador": jugador,
        "puntuacio": puntuacio,
        "files": files,
        "columnes": columnes,
        "data": data,
        "duracio_ms": duracio_ms
    }

    stats["rànquing_top5"].append(entrada)
    stats["rànquing_top5"] = sorted(stats["rànquing_top5"], key=lambda x: x["puntuacio"], reverse=True)[:5]

    with open(ruta_stats, "w") as archivo:
        json.dump(stats, archivo, indent=2)

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
@app.get("/iniciar/{filas}/{columnas}/{nombre_usuario}", tags=["Partida"])
def iniciar_partida(filas: int, columnas: int, nombre_usuario: str):
    partida_id, matriz, nombre_usuario = agregarMatrizPartida(partida, filas, columnas, nombre_usuario)

    partida[partida_id] = {
        "matriz": matriz,
        "barcos": {},
        "impactos": set(),
        "inicio": datetime.now(),
        "estado": "en_curs",
        "traza": [],
        "puntuacion": 0,
        "duracion_ms": 0,
        "jugador": nombre_usuario
    }

    resultado = agregarbarcos(partida, partida_id)
    guardar_temporal_partida(partida_id)
    return {
        "id": partida_id,
        "nombre": nombre_usuario,
        "matriz": resultado["matriz"],
        "barcos": resultado["barcos"]
    }

@app.get("/estadisticas", tags=["Estadisticas"])
def leerEstadisticas():
    ruta_stats = "../data/stats.json"

    if not os.path.exists(ruta_stats):
        return {
            "total_partides": 0,
            "millor_puntuacio": 0,
            "millor_jugador": "",
            "data_millor": "",
            "rànquing_top5": []
        }

    try:
        with open(ruta_stats, "r") as archivo:
            datos = json.load(archivo)
            # Asegurar que rànquing_top5 existe
            if "rànquing_top5" not in datos:
                datos["rànquing_top5"] = []
            return datos
    except Exception as e:
        return {
            "error": f"No s'ha pogut llegir el fitxer: {e}"
        }

@app.get("/tocados/{partida_id}/{x}/{y}")
def tocado(partida_id: str, x: int, y: int):
    datos = partida.get(partida_id)
    if datos is None:
        return {"error": "Partida no encontrada"}

    matriz = datos["matriz"]
    barcos = datos["barcos"]
    impactos = datos.setdefault("impactos", set())
    trazas = datos.setdefault("traza", [])

    if x < 0 or x >= len(matriz) or y < 0 or y >= len(matriz[0]):
        return {"error": "Coordenadas fuera de matriz"}

    valor = matriz[x][y]
    if valor == 0:
        impactos.add((x, y))  # registrar disparo fallido

        # Registrar traza de disparo fallido
        trazas.append({
            "coordenada": [x, y],
            "resultado": "Agua",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "resultado": "Agua",
            "estado": datos.get("estado", "en_curs"),
            "puntuacion": datos.get("puntuacion", 0)
        }

    impactos.add((x, y))

    tipo_barco = None
    id_barco = None
    destruido = False
    posiciones_destruidas = []

    for tipo, lista_barcos in barcos.items():
        for barco in lista_barcos:
            for pos in barco["posiciones"]:
                if pos[0] == x and pos[1] == y:
                    tipo_barco = tipo
                    id_barco = barco["id"]
                    posiciones_destruidas = barco["posiciones"].copy()
                    barco["posiciones"] = [
                        p for p in barco["posiciones"] if not (p[0] == x and p[1] == y)
                    ]
                    if len(barco["posiciones"]) == 0:
                        destruido = True
                    break
            if tipo_barco is not None:
                break

    # Calcular estado de partida
    casillas_destapadas = len(impactos)
    barcos_destruidos = sum(1 for b in barcos.values() for v in b if len(v["posiciones"]) == 0)
    total_barcos = sum(len(b) for b in barcos.values())
    estado = "en_curs"

    if barcos_destruidos == total_barcos:
        estado = "victoria"
    elif casillas_destapadas > 0.5 * len(matriz) * len(matriz[0]):
        estado = "derrota"

    if estado in ["victoria", "derrota"]:
        guardar_temporal_partida(partida_id)
        volcar_a_stats(partida_id)
    
    # Calcular puntuación
    encerts = sum(1 for x, y in impactos if matriz[x][y] != 0)
    dispars = casillas_destapadas
    inicio = datos.get("inicio", datetime.now())
    duracion = datetime.now() - inicio
    duracion_ms = int(duracion.total_seconds() * 1000)

    puntuacion = calcular_puntuacio(
        dispars=dispars,
        encerts=encerts,
        vaixells_enfonsats=barcos_destruidos,
        temps_inici=inicio,
        temps_final=datetime.now(),
        estat=estado
    )

    # Guardar estado y puntuación
    datos["estado"] = estado
    datos["puntuacion"] = puntuacion
    datos["duracion_ms"] = duracion_ms

    # Registrar traza del disparo exitoso
    trazas.append({
        "coordenada": [x, y],
        "resultado": "impacto",
        "tipo_barco": tipo_barco,
        "id_barco": id_barco,
        "destruido": destruido,
        "timestamp": datetime.now().isoformat()
    })

    respuesta = {
        "resultado": "impacto",
        "tipo_barco": tipo_barco,
        "id_barco": id_barco,
        "destruido": destruido,
        "barcos_destruidos": barcos_destruidos,
        "casillas_destapadas": casillas_destapadas,
        "estado": estado,
        "puntuacion": puntuacion
    }

    if destruido:
        respuesta["posiciones_destruidas"] = posiciones_destruidas

    return respuesta
    
@app.get("/estado_juego/{partida_id}", tags=["Estado_Juego"])
def estado_juego(partida_id: str):
    ruta = f"../data/games/{partida_id}.json"

    if not os.path.exists(ruta):
        return {"error": "Partida no trobada"}

    try:
        with open(ruta, "r") as archivo:
            dato = json.load(archivo)
            return dato
    except Exception as e:
        return {"error": f"No s'ha pogut llegir la partida: {e}"}
