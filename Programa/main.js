let tabla = document.getElementById("tablero"); 
let guardar = document.getElementById("guardar");
let estadisticas = document.getElementById("estadisticas");
let estado_juego = document.getElementById("estado_juego");
let partidaID = null;
let intervaloPuntuacion = null;
let dificultadSeleccionada = "medium";
let marcador = document.querySelector(".score");

guardar.addEventListener("click", (event) => {
  event.preventDefault();

  const nombre = document.getElementById("nombre");
  const ampliada = document.getElementById("ampliada");
  const altura = document.getElementById("altura");

  let camposInvalidos = [];
  if (nombre.value === "") camposInvalidos.push(nombre);
  if (ampliada.value === "") camposInvalidos.push(ampliada);
  if (altura.value === "") camposInvalidos.push(altura);

  if (camposInvalidos.length > 0) {
    camposInvalidos.forEach(campo => campo.setAttribute("class", "error"));

    const aviso = document.createElement("p");
    aviso.setAttribute("id", "aviso_campos");
    aviso.setAttribute("class", "error_mensaje");
    aviso.textContent = "Completa todos los campos antes de continuar.";

    estado_juego.innerHTML = "";
    estado_juego.appendChild(aviso);
    return;
  }

  [nombre, ampliada, altura].forEach(campo => campo.removeAttribute("class"));
  const avisoExistente = document.getElementById("aviso_campos");
  if (avisoExistente) avisoExistente.remove();

  fetch(`http://127.0.0.1:8000/iniciar/${ampliada.value}/${altura.value}/${nombre.value}/${dificultadSeleccionada}`)
    .then(response => response.json())
    .then(data => {
      partidaID = data.id;
      crearTabla(data.matriz);
      actualizarMarcador(data.puntuacion);

      fetch(`http://127.0.0.1:8000/estado_juego/${partidaID}`)
        .then(res => res.json())
        .then(info => {
          actualizarEstadisticasVisuales(info);
        });

      if (intervaloPuntuacion) clearInterval(intervaloPuntuacion);
      intervaloPuntuacion = setInterval(() => {
        fetch(`http://127.0.0.1:8000/puntuacio_actual/${partidaID}`)
          .then(res => res.json())
          .then(data => actualizarMarcador(data.puntuacion));
      }, 1000);
    });
});

tabla.addEventListener("click", (event) => {
  event.preventDefault();
  event.stopPropagation();
  const celda = event.target;
  if (celda.tagName !== "TD") return;
  if (celda.classList.contains("agua") || celda.classList.contains("impacto") || celda.classList.contains("hundido")) return;

  const x = celda.getAttribute("data-x");
  const y = celda.getAttribute("data-y");
  if (!partidaID) return;

  fetch(`http://127.0.0.1:8000/tocados/${partidaID}/${x}/${y}`)
    .then(res => res.json())
    .then(data => {
      celda.classList.remove("oculto");
      celda.setAttribute("data-activa", "false");

      actualizarMarcador(data.puntuacion);

      if (data.resultado === "Agua") {
        celda.setAttribute("class", "agua");
        celda.textContent = "O";
      } else if (data.resultado === "impacto") {
        celda.setAttribute("class", "impacto");
        celda.textContent = "X";

        if (data.destruido && data.posiciones_destruidas) {
          data.posiciones_destruidas.forEach(([bx, by]) => {
            const celdaHundida = document.querySelector(`td[data-x="${bx}"][data-y="${by}"]`);
            if (celdaHundida) {
              celdaHundida.setAttribute("class", "hundido");
              celdaHundida.setAttribute("data-activa", "false");
              celdaHundida.textContent = "☠️";
            }
          });
        }
      }

      fetch(`http://127.0.0.1:8000/estado_juego/${partidaID}`)
        .then(res => res.json())
        .then(info => {
          actualizarEstadisticasVisuales(info);

          if (data.estado === "victoria" || data.estado === "derrota") {
            clearInterval(intervaloPuntuacion);
            mostrarEstadoFinal(info);
            document.querySelectorAll("#tablero td").forEach(celda => {
              celda.setAttribute("data-activa", "false");
            });
            alert(info.estat === "victoria" ? "🎉 Has ganado!" : "💀 Has perdido...");
          }
        });
    })
    .catch(err => console.error("Error al disparar:", err));
});

estadisticas.addEventListener("click", (event) => {
  event.preventDefault();
  fetch("http://127.0.0.1:8000/estadisticas")
    .then(response => response.json())
    .then(data => {
      document.getElementById("total_partides").textContent = data.total_partides;
      document.getElementById("millor_puntuacio").textContent = data.millor_puntuacio;
      document.getElementById("millor_jugador").textContent = data.millor_jugador;
      document.getElementById("data_millor").textContent = data.data_millor;

      const rankingList = document.getElementById("ranking_list");
      rankingList.innerHTML = "";
      data.rànquing_top5.forEach(p => {
        const li = document.createElement("li");
        li.textContent = `${p.jugador} - ${p.puntuacio} puntos (${p.files}x${p.columnes})`;
        rankingList.appendChild(li);
      });
    })
    .catch(error => console.error("Error al obtener estadísticas:", error));
});

document.getElementById("ver_estado").addEventListener("click", () => {
  if (!partidaID) return alert("No hay partida activa");

  fetch(`http://127.0.0.1:8000/estado_juego/${partidaID}`)
    .then(res => res.json())
    .then(data => {
      estado_juego.innerHTML = "";
      const titulo = document.createElement("h4");
      titulo.textContent = "Estado de la partida";
      estado_juego.appendChild(titulo);

      const datos = [
        ["Jugador:", data.jugador],
        ["Estado:", data.estat],
        ["Dificultad:", dificultadSeleccionada],
        ["Barcos hundidos:", `${data.vaixells_enfonsats} / ${data.vaixells_totals}`],
        ["Casillas destapadas:", data.caselles_destapades],
        ["Inicio:", data.data_inici],
        ["Fin:", data.data_fi || "En curso..."]
      ];

      datos.forEach(([label, valor]) => {
        const p = document.createElement("p");
        p.textContent = `${label} ${valor}`;
        estado_juego.appendChild(p);
      });
    })
    .catch(error => console.error("Error al obtener estado de juego:", error));
});

document.querySelector(".btn.rojo").addEventListener("click", (event) => {
  event.preventDefault();
  event.stopPropagation();
  if (!partidaID) return alert("No hay partida activa");

  clearInterval(intervaloPuntuacion);
  fetch(`http://127.0.0.1:8000/abandonar/${partidaID}`)
    .then(res => res.json())
    .then(data => {
      estado_juego.innerHTML = "";
      const titulo = document.createElement("h4");
      titulo.textContent = "Partida abandonada";
      estado_juego.appendChild(titulo);

      const datos = [
        ["Jugador:", data.jugador],
        ["Estado:", data.estat],
        ["Dificultad:", dificultadSeleccionada],
        ["Puntuación:", data.puntuacio],
        ["Barcos hundidos:", data.vaixells_enfonsats],
        ["Casillas destapadas:", data.caselles_destapades]
      ];

      datos.forEach(([label, valor]) => {
        const p = document.createElement("p");
        p.textContent = `${label} ${valor}`;
        estado_juego.appendChild(p);
      });
    });
});

function crearTabla(matriz) {
  const tablero = document.querySelector("#tablero tbody");
  tablero.innerHTML = "";

  for (let i = 0; i < matriz.length; i++) {
    const fila = document.createElement("tr");
    for (let j = 0; j < matriz[i].length; j++) {
      const celda = document.createElement("td");
      celda.setAttribute("data-x", i);
      celda.setAttribute("data-y", j);
      celda.setAttribute("data-valor", matriz[i][j]);
      celda.setAttribute("class", "oculto");
      fila.appendChild(celda);
    }
    tablero.appendChild(fila);
  }
}

function actualizarMarcador(puntuacion) {
  marcador.textContent = `${puntuacion} puntos`;
  actualizarColor(puntuacion);
}

function actualizarColor(puntuacion) {
  const nivel =
    puntuacion >= 500 ? "alta" :
    puntuacion >= 200 ? "media" :
    "baja";
  marcador.setAttribute("class", `score ${dificultadSeleccionada} ${nivel}`);
}

function mostrarEstadoFinal(info) {
  estado_juego.innerHTML = "";
  const titulo = document.createElement("h4");
  titulo.textContent = `Partida ${info.estat}`;
  estado_juego.appendChild(titulo);

  const datos = [
    ["Jugador:", info.jugador],
    ["Dificultad:", dificultadSeleccionada],
    ["Puntuación:", info.puntuacion],
    ["Barcos hundidos:", `${info.vaixells_enfonsats} / ${info.vaixells_totals}`],
    ["Casillas destapadas:", info.caselles_destapades],
    ["Inicio:", info.data_inici],
    ["Fin:", info.data_fi]
  ];

  datos.forEach(([label, valor]) => {
    const p = document.createElement("p");
    p.textContent = `${label} ${valor}`;
    estado_juego.appendChild(p);
  });
}

function actualizarEstadisticasVisuales(data) {
  document.getElementById("jugador").textContent = `Jugador: ${data.jugador}`;
  document.querySelector(".container h4").textContent = `Estado: ${data.estat}`;

  const stats = document.querySelectorAll(".stat");
  stats[0].textContent = `Hits: ${data.impactos_barco}`;
  stats[1].textContent = `Misses: ${data.impactos_agua}`;
  stats[2].textContent = `Ships Sunk: ${data.vaixells_enfonsats}`;

  document.getElementById("jugadas").textContent = data.caselles_destapades;
}
