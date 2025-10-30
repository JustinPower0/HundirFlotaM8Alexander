from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

#Calcula la puntuacion
def calcular_puntuacio(dispars, encerts, vaixells_enfonsats, temps_inici, temps_final, estat, dificultat="easy"):
    BASE = 1000

    if estat == "abandonada":
        return 0

    # Ajustes según dificultad
    if dificultat == "easy":
        COST_DISPAR = -5
        PENAL_TEMPS = -0.5
        MULTIPLICADOR = 1.0
    elif dificultat == "hard":
        COST_DISPAR = -20
        PENAL_TEMPS = -2
        MULTIPLICADOR = 1.5
    else:  # medium
        COST_DISPAR = -10
        PENAL_TEMPS = -1
        MULTIPLICADOR = 2.0

    BONUS_ENCERT = 20
    BONUS_ENFONSAT = 50

    duracio = (temps_final - temps_inici).total_seconds()
    puntuacio_base  = (
        BASE +
        dispars * COST_DISPAR +
        encerts * BONUS_ENCERT +
        vaixells_enfonsats * BONUS_ENFONSAT +
        int(duracio) * PENAL_TEMPS
    )
    puntuacio_final = int(puntuacio_base * MULTIPLICADOR)
    return max(puntuacio_final, 0)

#Para saber que umbral de dificultat estoy
def umbral_derrota(dificultat="easy"):
    if dificultat == "hard":
        return 0.35
    elif dificultat == "medium":
        return 0.45
    else:  # easy
        return 0.5

#Volcar los datos en disco
def volcar_partida_finalizada(partida_id: str):
    datos = partida.get(partida_id)
    if not datos or datos.get("estado") == "en_curs":
        return

    # Rutas absolutas desde /fastApi hacia /data
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    GAMES_DIR = os.path.join(DATA_DIR, "games")
    STATS_FILE = os.path.join(DATA_DIR, "stats.json")

    os.makedirs(GAMES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # Limpiar datos no serializables
    datos_limpios = datos.copy()
    datos_limpios["inicio"] = datos_limpios["inicio"].isoformat() if isinstance(datos_limpios["inicio"], datetime) else datos_limpios["inicio"]
    datos_limpios["impactos"] = list(datos_limpios.get("impactos", []))
    datos_limpios["data_fi"] = datos_limpios.get("data_fi", datetime.now().isoformat())

    # Guardar partida completa
    ruta_partida = os.path.join(GAMES_DIR, f"{partida_id}.json")
    with open(ruta_partida, "w", encoding="utf-8") as f:
        json.dump(datos_limpios, f, indent=2, ensure_ascii=False)

    # Preparar datos para stats.json
    puntuacio = datos.get("puntuacion", 0)
    jugador = datos.get("jugador", "anònim")
    files = len(datos["matriz"])
    columnes = len(datos["matriz"][0])
    data_fi = datos_limpios["data_fi"]
    data_inici = datos.get("inicio", datetime.now())
    if isinstance(data_inici, str):
        data_inici = datetime.fromisoformat(data_inici)
    duracio_ms = int((datetime.fromisoformat(data_fi) - data_inici).total_seconds() * 1000)

    # Cargar o crear stats.json
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if not contenido:
                raise ValueError("stats.json está vacío")
            stats = json.loads(contenido)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        stats = {
            "total_partides": 0,
            "millor_puntuacio": 0,
            "millor_jugador": "",
            "data_millor": "",
            "rànquing_top5": []
        }

    # Actualizar estadísticas
    stats["total_partides"] += 1

    if puntuacio > stats["millor_puntuacio"]:
        stats["millor_puntuacio"] = puntuacio
        stats["millor_jugador"] = jugador
        stats["data_millor"] = data_fi

    stats["rànquing_top5"].append({
        "jugador": jugador,
        "puntuacio": puntuacio,
        "files": files,
        "columnes": columnes,
        "data": data_fi,
        "duracio_ms": duracio_ms
    })

    stats["rànquing_top5"] = sorted(stats["rànquing_top5"], key=lambda x: x["puntuacio"], reverse=True)[:5]

    # Guardar stats.json
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

# Crear la aplicación
app = FastAPI(title="Mi Projecto", version="0.0.1")

# Lista de orígenes permitidos
origins = [
    "http://localhost:5500",  # si tu frontend corre aquí
    "http://127.0.0.1:5500",
]

#Cors
app.add_middleware(
    CORSMiddleware,
     #allow_origins=["*"],  # permite cualquier origen (no recomendable en producción)
    allow_origins=origins,  # permite solo esos orígenes
    allow_credentials=True,
    allow_methods=["*"],    # permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],    # permite todas las cabeceras
)

# Funciones FastApi
#Funcion para iniciar la partida
@app.get("/iniciar/{filas}/{columnas}/{nombre_usuario}/{dificultat}", tags=["Partida"])
def iniciar_partida(filas: int, columnas: int, nombre_usuario: str, dificultat: str = "medium"):
    partida_id, matriz, nombre_usuario = agregarMatrizPartida(partida, filas, columnas, nombre_usuario)

    inicio = datetime.now()
    partida[partida_id] = {
        "matriz": matriz,
        "barcos": {},
        "impactos": set(),
        "inicio": inicio,
        "estado": "en_curs",
        "dificultat": dificultat,
        "traza": [],
        "puntuacion": 0,
        "duracion_ms": 0,
        "jugador": nombre_usuario
    }

    resultado = agregarbarcos(partida, partida_id)

    # Calcular puntuación inicial
    puntuacion_inicial = calcular_puntuacio(
        dispars=0,
        encerts=0,
        vaixells_enfonsats=0,
        temps_inici=inicio,
        temps_final=inicio,
        estat="en_curs"
    )

    partida[partida_id]["puntuacion"] = puntuacion_inicial

    return {
        "id": partida_id,
        "nombre": nombre_usuario,
        "matriz": resultado["matriz"],
        "barcos": resultado["barcos"],
        "puntuacion": puntuacion_inicial
    }
#Funcion para ver las estadisticas
@app.get("/estadisticas", tags=["Estadisticas"])
def leerEstadisticas():
    ruta_stats = "../data/stats.json"

    if not os.path.exists(ruta_stats):
        return {
            "total_partides": 0,
            "millor_puntuacio": 0,
            "millor_jugador": "",
            "data_millor": "",
            "rànquing": []
        }

    try:
        with open(ruta_stats, "r", encoding="utf-8") as archivo:
            contenido = archivo.read().strip()
            if not contenido:
                raise ValueError("El fitxer està buit")

            datos = json.loads(contenido)

            return datos

    except (json.JSONDecodeError, ValueError) as e:
        return {
            "total_partides": 0,
            "millor_puntuacio": 0,
            "millor_jugador": "",
            "data_millor": "",
            "rànquing": [],
            "error": f"Fitxer mal format o buit: {e}"
        }

    except Exception as e:
        return {
            "error": f"No s'ha pogut llegir el fitxer: {e}"
        }
#Funcion para hacer los disparos a los barcos
@app.get("/tocados/{partida_id}/{x}/{y}", tags=["Disparo"])
def tocado(partida_id: str, x: int, y: int):
    datos = partida.get(partida_id)
    if datos is None:
        return {"error": "Partida no encontrada"}

    matriz = datos["matriz"]
    barcos = datos["barcos"]
    impactos = datos.setdefault("impactos", set())
    trazas = datos.setdefault("traza", [])
    datos.setdefault("impactos_barco", 0)
    datos.setdefault("impactos_agua", 0)

    if x < 0 or x >= len(matriz) or y < 0 or y >= len(matriz[0]):
        return {"error": "Coordenadas fuera de matriz"}

    valor = matriz[x][y]
    if valor == 0:
        impactos.add((x, y))  # registrar disparo fallido
        datos["impactos_agua"] += 1

        # Registrar traza de disparo fallido
        trazas.append({
            "coordenada": [x, y],
            "resultado": "Agua",
            "timestamp": datetime.now().isoformat()
        })

        encerts = sum(1 for x, y in impactos if matriz[x][y] != 0)
        dispars = len(impactos)
        inicio = datos.get("inicio", datetime.now())
        puntuacion = calcular_puntuacio(
        dispars=dispars,
        encerts=encerts,
        vaixells_enfonsats=sum(1 for b in barcos.values() for v in b if len(v["posiciones"]) == 0),
        temps_inici=inicio,
        temps_final=datetime.now(),
        estat=datos.get("estado", "en_curs")
        )
        datos["puntuacion"] = puntuacion
        return {
        "resultado": "Agua",
        "estado": datos.get("estado", "en_curs"),
        "puntuacion": puntuacion
        }

    impactos.add((x, y))
    datos["impactos_barco"] += 1

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
    elif casillas_destapadas > umbral_derrota(datos.get("dificultat", "easy")) * len(matriz) * len(matriz[0]):
        estado = "derrota"

    datos["estado"] = estado

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

    datos["puntuacion"] = puntuacion
    datos["duracion_ms"] = duracion_ms

    # Volcar si es final
    if estado in ["victoria", "derrota"]:
        volcar_partida_finalizada(partida_id)

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

#Funcion para ver el estado del juego en la memoria
@app.get("/estado_juego/{partida_id}", tags=["Estado_Juego"])
def estado_juego(partida_id: str):
    datos = partida.get(partida_id)
    if not datos:
        return {"error": "Partida no trobada"}

    jugador = datos.get("jugador", "anònim")
    estat = datos.get("estado", "en_curs")
    dificultat = datos.get("dificultat", "medium")
    puntuacio = datos.get("puntuacion", 0)
    data_inici = datos["inicio"].isoformat() if isinstance(datos["inicio"], datetime) else datos["inicio"]
    data_fi = datos.get("data_fi", None)
    duracion_ms = datos.get("duracion_ms", 0)
    impactos = datos.get("impactos", [])
    matriz = datos.get("matriz", [])
    barcos = datos.get("barcos", {})

    vaixells_enfonsats = sum(1 for b in barcos.values() for v in b if len(v["posiciones"]) == 0)
    vaixells_totals = sum(len(b) for b in barcos.values())
    caselles_destapades = len(impactos)

    impactos_barco = datos.get("impactos_barco", 0)
    impactos_agua = datos.get("impactos_agua", 0)

    return {
        "jugador": jugador,
        "estat": estat,
        "dificultat": dificultat,
        "puntuacio": puntuacio,
        "data_inici": data_inici,
        "data_fi": data_fi,
        "duracion_ms": duracion_ms,
        "vaixells_enfonsats": vaixells_enfonsats,
        "vaixells_totals": vaixells_totals,
        "caselles_destapades": caselles_destapades,
        "impactos_barco": impactos_barco,
        "impactos_agua": impactos_agua,
    }
#Funcion para ir actualizando la puntuacion a tiempo real
@app.get("/puntuacio_actual/{partida_id}", tags=["Partida"])
def puntuacio_actual(partida_id: str):
    datos = partida.get(partida_id)
    if not datos:
        return {"error": "Partida no trobada"}

    matriz = datos["matriz"]
    impactos = datos.get("impactos", set())
    barcos = datos.get("barcos", {})
    inicio = datos.get("inicio", datetime.now())
    estat = datos.get("estado", "en_curs")

    encerts = sum(1 for x, y in impactos if matriz[x][y] != 0)
    dispars = len(impactos)
    vaixells_enfonsats = sum(1 for b in barcos.values() for v in b if len(v["posiciones"]) == 0)

    puntuacio = calcular_puntuacio(
        dispars=dispars,
        encerts=encerts,
        vaixells_enfonsats=vaixells_enfonsats,
        temps_inici=inicio,
        temps_final=datetime.now(),
        estat=estat
    )

    datos["puntuacion"] = puntuacio

    return {"puntuacion": puntuacio}
#Funcion para abandonar el juego
@app.get("/abandonar/{partida_id}", tags=["Partida"])
def abandonar_partida(partida_id: str):
    datos = partida.get(partida_id)
    if not datos:
        return {"error": "Partida no trobada"}

    datos["estado"] = "abandonada"
    datos["data_fi"] = datetime.now().isoformat()
    datos["puntuacion"] = 0

    volcar_partida_finalizada(partida_id)

    return {
        "jugador": datos["jugador"],
        "estat": datos["estado"],
        "puntuacio": datos.get("puntuacion", 0),
        "vaixells_enfonsats": datos.get("vaixells_enfonsats", 0),
        "caselles_destapades": len(datos.get("impactos", []))
    }