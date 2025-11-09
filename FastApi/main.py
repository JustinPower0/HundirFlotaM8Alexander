from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import uuid
import json
import os
from datetime import datetime

partida = {}
barcos_definicion = {
    "submari": {"id": 1, "longitud": 1},
    "destructor": {"id": 2, "longitud": 2},
    "creuer": {"id": 3, "longitud": 3},
    "cuirassat": {"id": 4, "longitud": 4},
    "portaavions": {"id": 5, "longitud": 5}
}

# Funciones de utilidad
def crearMatriz(filas,columnas):
    return [[0 for _ in range(columnas)] for _ in range(filas)]

def agregarMatrizPartida(partida, filas, columnas, nombre_usuario):
    matriz = crearMatriz(filas,columnas)
    partida_id = str(uuid.uuid4())
    partida[partida_id] = {
        "matriz": matriz,
        "jugador": nombre_usuario,
        "barcos": {}
    }
    return partida_id, matriz, nombre_usuario

def agregarBarcos(partida, partida_id):
    datos = partida.get(partida_id)
    if datos is None:
        return {"error": "Partida no encontrada"}
    
    matriz = datos["matriz"]
    filas, columnas = len(matriz), len(matriz[0])
    total_casillas = filas * columnas
    limite_ocupacion = int(total_casillas * 0.3)

    barcos = {}
    estado = {"ocupadas": 0}
    id_por_tipo = {nombre: 1 for nombre in barcos_definicion}

    def colocar_barco(nombre, info):
        tipo, longitud = info["id"], info["longitud"]
        intentos = 0
        while intentos < 100:
            orientacion = random.choice(["horizontal", "vertical"])
            if orientacion == "horizontal":
                fila = random.randint(0, filas-1)
                col = random.randint(0, columnas-longitud)
                posiciones = [(fila, col+i) for i in range(longitud)]
            else:
                fila = random.randint(0, filas-longitud)
                col = random.randint(0, columnas-1)
                posiciones = [(fila+i, col) for i in range(longitud)]
            if all(matriz[x][y] == 0 for x,y in posiciones):
                for x,y in posiciones:
                    matriz[x][y] = tipo
                barcos.setdefault(nombre, []).append({
                    "id": id_por_tipo[nombre],
                    "posiciones": posiciones
                })
                id_por_tipo[nombre] += 1
                estado["ocupadas"] += longitud
                return True
            intentos += 1
        return False

    for nombre, info in barcos_definicion.items():
        if not colocar_barco(nombre, info):
            return {"error": f"No se pudo colocar el barco {nombre}"}

    while estado["ocupadas"] < limite_ocupacion:
        nombre, info = random.choice(list(barcos_definicion.items()))
        if estado["ocupadas"] + info["longitud"] > limite_ocupacion:
            break
        colocar_barco(nombre, info)

    datos["barcos"] = barcos
    return {"matriz": matriz, "barcos": barcos}

def calcularPuntuacio(dispars, encerts, vaixells_enfonsats, temps_inici, temps_final, estat, dificultat="easy"):
    BASE = 1000
    if estat == "abandonada":
        return 0

    if dificultat == "easy":
        COST_DISPAR, PENAL_TEMPS, MULTIPLICADOR = -5, -0.5, 1.0
    elif dificultat == "hard":
        COST_DISPAR, PENAL_TEMPS, MULTIPLICADOR = -20, -2, 1.5
    else:  # medium
        COST_DISPAR, PENAL_TEMPS, MULTIPLICADOR = -10, -1, 2.0

    BONUS_ENCERT, BONUS_ENFONSAT = 20, 50
    duracio = (temps_final - temps_inici).total_seconds()
    puntuacio_base = BASE + dispars*COST_DISPAR + encerts*BONUS_ENCERT + vaixells_enfonsats*BONUS_ENFONSAT + int(duracio)*PENAL_TEMPS
    puntuacio_final = int(puntuacio_base*MULTIPLICADOR)
    return max(puntuacio_final, 0)

def umbralDerrota(dificultat="easy"):
    if dificultat=="hard": return 0.35
    elif dificultat=="medium": return 0.45
    return 0.5

def volcarPartidaFinalizada(partida_id: str):
    datos = partida.get(partida_id)
    if not datos or datos.get("estado")=="en_curs":
        return
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR = os.path.join(BASE_DIR,"data")
    GAMES_DIR = os.path.join(DATA_DIR,"games")
    STATS_FILE = os.path.join(DATA_DIR,"stats.json")
    os.makedirs(GAMES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    datos_limpios = datos.copy()
    datos_limpios["inicio"] = datos_limpios["inicio"].isoformat() if isinstance(datos_limpios["inicio"], datetime) else datos_limpios["inicio"]
    datos_limpios["impactos"] = datos_limpios.get("impactos", [])
    datos_limpios["data_fi"] = datos_limpios.get("data_fi", datetime.now().isoformat())

    ruta_partida = os.path.join(GAMES_DIR, f"{partida_id}.json")
    with open(ruta_partida, "w", encoding="utf-8") as f:
        json.dump(datos_limpios, f, indent=2, ensure_ascii=False)

    puntuacio = datos.get("puntuacion",0)
    jugador = datos.get("jugador","anònim")
    files = len(datos["matriz"])
    columnes = len(datos["matriz"][0])
    data_fi = datos_limpios["data_fi"]
    data_inici = datos.get("inicio",datetime.now())
    if isinstance(data_inici,str): data_inici = datetime.fromisoformat(data_inici)
    duracio_ms = int((datetime.fromisoformat(data_fi) - data_inici).total_seconds()*1000)

    try:
        with open(STATS_FILE,"r",encoding="utf-8") as f:
            contenido = f.read().strip()
            if not contenido: raise ValueError("stats.json está vacío")
            stats = json.loads(contenido)
    except (FileNotFoundError,json.JSONDecodeError,ValueError):
        stats = {
            "total_partides":0,
            "millor_puntuacio":0,
            "millor_jugador":"",
            "data_millor":"",
            "rànquing_top5":[]
        }

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
    stats["rànquing_top5"] = sorted(stats["rànquing_top5"], key=lambda x:x["puntuacio"], reverse=True)[:5]

    with open(STATS_FILE,"w",encoding="utf-8") as f:
        json.dump(stats,f,indent=2,ensure_ascii=False)

# Crear app FastAPI
app = FastAPI(title="Mi Projecto", version="0.0.1")


origins = ["http://localhost:5500","http://127.0.0.1:5500"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---
@app.get("/iniciar/{filas}/{columnas}/{nombre_usuario}/{dificultat}", tags=["Partida"])
def iniciarPartida(filas: int, columnas: int, nombre_usuario: str, dificultat: str = "easy"):
    partida_id, matriz, nombre_usuario = agregarMatrizPartida(partida, filas, columnas, nombre_usuario)
    inicio = datetime.now()
    partida[partida_id] = {
        "matriz": matriz,
        "barcos": {},
        "impactos": [],
        "inicio": inicio,
        "estado": "en_curs",
        "dificultat": dificultat,
        "traza": [],
        "puntuacion": 0,
        "duracion_ms": 0,
        "jugador": nombre_usuario
    }
    resultado = agregarBarcos(partida, partida_id)
    puntuacion_inicial = calcularPuntuacio(0,0,0,inicio,inicio,"en_curs")
    partida[partida_id]["puntuacion"] = puntuacion_inicial
    return {"id":partida_id,"nombre":nombre_usuario,"matriz":resultado["matriz"],"barcos":resultado["barcos"],"puntuacion":puntuacion_inicial}

@app.get("/tocados/{partida_id}/{x}/{y}", tags=["Disparo"])
def tocado(partida_id: str, x:int, y:int):
    datos = partida.get(partida_id)
    if not datos: return {"error":"Partida no encontrada"}
    matriz = datos["matriz"]
    barcos = datos["barcos"]
    impactos = datos.setdefault("impactos",[])
    trazas = datos.setdefault("traza",[])
    datos.setdefault("impactos_barco",0)
    datos.setdefault("impactos_agua",0)

    if x<0 or x>=len(matriz) or y<0 or y>=len(matriz[0]): return {"error":"Coordenadas fuera de matriz"}
    valor = matriz[x][y]
    if [x,y] not in impactos: impactos.append([x,y])
    if valor==0: datos["impactos_agua"]+=1; resultado_texto="Agua"
    else: datos["impactos_barco"]+=1; resultado_texto="impacto"

    trazas.append({"coordenada":[x,y],"resultado":resultado_texto,"timestamp":datetime.now().isoformat()})

    tipo_barco = None; id_barco=None; destruido=False; posiciones_destruidas=[]
    if valor!=0:
        for tipo, lista_barcos in barcos.items():
            for barco in lista_barcos:
                for pos in barco["posiciones"]:
                    if pos[0]==x and pos[1]==y:
                        tipo_barco = tipo; id_barco=barco["id"]
                        posiciones_destruidas = barco["posiciones"].copy()
                        barco["posiciones"] = [p for p in barco["posiciones"] if not (p[0]==x and p[1]==y)]
                        if len(barco["posiciones"])==0: destruido=True
                        break
                if tipo_barco is not None: break

    casillas_destapadas=len(impactos)
    barcos_destruidos=sum(1 for b in barcos.values() for v in b if len(v["posiciones"])==0)
    total_barcos=sum(len(b) for b in barcos.values())
    estado="en_curs"
    if barcos_destruidos==total_barcos: estado="victoria"
    elif casillas_destapadas>umbralDerrota(datos.get("dificultat","easy"))*len(matriz)*len(matriz[0]): estado="derrota"
    datos["estado"]=estado

    encerts=sum(1 for cx,cy in impactos if matriz[cx][cy]!=0)
    dispars=casillas_destapadas
    puntuacion=calcularPuntuacio(dispars,encerts,barcos_destruidos,datos.get("inicio",datetime.now()),datetime.now(),estado)
    datos["puntuacion"]=puntuacion
    datos["duracion_ms"]=int((datetime.now()-datos.get("inicio",datetime.now())).total_seconds()*1000)

    if estado in ["victoria","derrota"]: volcarPartidaFinalizada(partida_id)

    respuesta={"resultado":resultado_texto,"tipo_barco":tipo_barco,"id_barco":id_barco,"destruido":destruido,"barcos_destruidos":barcos_destruidos,"casillas_destapadas":casillas_destapadas,"estado":estado,"puntuacion":puntuacion}
    if destruido: respuesta["posiciones_destruidas"]=posiciones_destruidas
    return respuesta

@app.get("/estado_juego/{partida_id}", tags=["Estado_Juego"])
def estadoJuego(partida_id:str):
    datos=partida.get(partida_id)
    if not datos: return {"error":"Partida no trobada"}
    jugador=datos.get("jugador","anònim")
    estat=datos.get("estado","en_curs")
    dificultat=datos.get("dificultat","medium")
    puntuacio=datos.get("puntuacion",0)
    data_inici=datos["inicio"].isoformat() if isinstance(datos["inicio"],datetime) else datos["inicio"]
    data_fi=datos.get("data_fi",None)
    duracion_ms=datos.get("duracion_ms",0)
    impactos=datos.get("impactos",[])
    matriz=datos.get("matriz",[])
    barcos=datos.get("barcos",{})

    vaixells_enfonsats=sum(1 for b in barcos.values() for v in b if len(v["posiciones"])==0)
    vaixells_totals=sum(len(b) for b in barcos.values())
    caselles_destapades=len(impactos)
    impactos_barco=datos.get("impactos_barco",0)
    impactos_agua=datos.get("impactos_agua",0)

    return {"jugador":jugador,"estat":estat,"dificultat":dificultat,"puntuacio":puntuacio,"data_inici":data_inici,"data_fi":data_fi,"duracion_ms":duracion_ms,"vaixells_enfonsats":vaixells_enfonsats,"vaixells_totals":vaixells_totals,"caselles_destapades":caselles_destapades,"impactos_barco":impactos_barco,"impactos_agua":impactos_agua}

@app.get("/puntuacio_actual/{partida_id}", tags=["Partida"])
def puntuacioActual(partida_id:str):
    datos=partida.get(partida_id)
    if not datos: return {"error":"Partida no trobada"}
    matriz=datos["matriz"]
    impactos=datos.get("impactos",[])
    barcos=datos.get("barcos",{})
    inicio=datos.get("inicio",datetime.now())
    estat=datos.get("estado","en_curs")
    encerts=sum(1 for x,y in impactos if matriz[x][y]!=0)
    dispars=len(impactos)
    vaixells_enfonsats=sum(1 for b in barcos.values() for v in b if len(v["posiciones"])==0)
    puntuacio=calcularPuntuacio(dispars,encerts,vaixells_enfonsats,inicio,datetime.now(),estat)
    datos["puntuacion"]=puntuacio
    return {"puntuacion":puntuacio}

@app.get("/abandonar/{partida_id}", tags=["Partida"])
def abandonarPartida(partida_id:str):
    datos=partida.get(partida_id)
    if not datos: return {"error":"Partida no trobada"}
    datos["estado"]="abandonada"
    datos["data_fi"]=datetime.now().isoformat()
    datos["puntuacion"]=0
    volcarPartidaFinalizada(partida_id)
    return {"jugador":datos["jugador"],"estat":datos["estado"],"puntuacio":datos.get("puntuacion",0),"vaixells_enfonsats":datos.get("vaixells_enfonsats",0),"caselles_destapades":len(datos.get("impactos",[]))}
