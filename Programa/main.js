let tabla = document.getElementById("tablero");
let guardar = document.getElementById("guardar");
let estadisticas = document.getElementById("estadisticas");
let estado_juego = document.getElementById("estado_juego");
let partidaID = null;
let intervaloPuntuacion = null;
let dificultadSeleccionada = "medium"; // valor por defecto

const marcador = document.createElement("div");
marcador.setAttribute("id", "puntos");
marcador.appendChild(document.createTextNode("Punts: 0"));
document.body.appendChild(marcador);

guardar.addEventListener("click", (event) => {
  event.preventDefault();
  const nombre = document.getElementById("nombre").value;
  const ampliada = document.getElementById("ampliada").value;
  const altura = document.getElementById("altura").value;
  dificultadSeleccionada = document.querySelector('input[name="dificultat"]:checked').value;

  if (nombre === "" || ampliada === "" || altura === "") return;

  fetch(`http://127.0.0.1:8000/iniciar/${ampliada}/${altura}/${nombre}/${dificultadSeleccionada}`)
    .then(response => response.json())
    .then(data => {
      partidaID = data.id;
      crearTabla(data.matriz);

      actualizarMarcador(data.puntuacion);

      if (intervaloPuntuacion) clearInterval(intervaloPuntuacion);
      intervaloPuntuacion = setInterval(() => {
        fetch(`http://127.0.0.1:8000/puntuacio_actual/${partidaID}`)
          .then(res => res.json())
          .then(data => {
            actualizarMarcador(data.puntuacion);
          });
      }, 1000);
    });
});

tabla.addEventListener("click", event => {
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
              celdaHundida.innerHTML = "";
              celdaHundida.appendChild(document.createTextNode("☠️"));
            }
          });
        }
      }

      if (data.estado === "victoria" || data.estado === "derrota") {
        clearInterval(intervaloPuntuacion);
        fetch(`http://127.0.0.1:8000/estado_juego/${partidaID}`)
          .then(res => res.json())
          .then(info => {
            mostrarEstadoFinal(info);
            document.querySelectorAll("#tablero td").forEach(celda => {
              celda.setAttribute("data-activa", "false");
            });
            alert(info.estat === "victoria" ? "🎉 Has guanyat la partida!" : "💀 Has perdut la partida...");
          });
      }
    })
    .catch(err => console.error("Error al disparar:", err));
});

estadisticas.addEventListener("click", (event) => {
  event.preventDefault();
  fetch("http://127.0.0.1:8000/estadisticas")
    .then(response => response.json())
    .then(data => {
      estado_juego.innerHTML = "";
      const titulo = document.createElement("h4");
      titulo.appendChild(document.createTextNode("Estadístiques globals"));
      estado_juego.appendChild(titulo);

      const datos = [
        [`Total partides:`, data.total_partides],
        [`Millor puntuació:`, `${data.millor_puntuacio} (${data.millor_jugador})`],
        [`Data millor:`, data.data_millor]
      ];

      datos.forEach(([label, valor]) => {
        const p = document.createElement("p");
        p.appendChild(document.createTextNode(`${label} ${valor}`));
        estado_juego.appendChild(p);
      });

      const subtitulo = document.createElement("h5");
      subtitulo.appendChild(document.createTextNode("Rànquing:"));
      estado_juego.appendChild(subtitulo);

      const lista = document.createElement("ol");
      data.rànquing_top5.forEach(p => {
        const li = document.createElement("li");
        li.appendChild(document.createTextNode(`${p.jugador} - ${p.puntuacio} punts (${p.files}x${p.columnes})`));
        lista.appendChild(li);
      });
      estado_juego.appendChild(lista);
    })
    .catch(error => console.error("Error al obtener estadísticas:", error));
});

document.getElementById("ver_estado").addEventListener("click", () => {
  if (!partidaID) return alert("No hi ha partida activa");

  fetch(`http://127.0.0.1:8000/estado_juego/${partidaID}`)
    .then(res => res.json())
    .then(data => {
      estado_juego.innerHTML = "";
      const titulo = document.createElement("h4");
      titulo.appendChild(document.createTextNode("Estat de la partida"));
      estado_juego.appendChild(titulo);

      const datos = [
        [`Jugador:`, data.jugador],
        [`Estat:`, data.estat],
        [`Dificultat:`, dificultadSeleccionada],
        [`Vaixells enfonsats:`, `${data.vaixells_enfonsats} / ${data.vaixells_totals}`],
        [`Caselles destapades:`, data.caselles_destapades],
        [`Inici:`, data.data_inici],
        [`Fi:`, data.data_fi || "En curs..."]
      ];

      datos.forEach(([label, valor]) => {
        const p = document.createElement("p");
        p.appendChild(document.createTextNode(`${label} ${valor}`));
        estado_juego.appendChild(p);
      });
    })
    .catch(error => console.error("Error al obtener estado de juego:", error));
});

document.querySelector(".btn.rojo").addEventListener("click", () => {
  if (!partidaID) return alert("No hi ha partida activa");

  clearInterval(intervaloPuntuacion);
  fetch(`http://127.0.0.1:8000/abandonar/${partidaID}`)
    .then(res => res.json())
    .then(data => {
      estado_juego.innerHTML = "";
      const titulo = document.createElement("h4");
      titulo.appendChild(document.createTextNode("Partida abandonada"));
      estado_juego.appendChild(titulo);

      const datos = [
        [`Jugador:`, data.jugador],
        [`Estat:`, data.estat],
        [`Dificultat:`, dificultadSeleccionada],
        [`Puntuació:`, data.puntuacio],
        [`Vaixells enfonsats:`, data.vaixells_enfonsats],
        [`Caselles destapades:`, data.caselles_destapades]
      ];

      datos.forEach(([label, valor]) => {
        const p = document.createElement("p");
        p.appendChild(document.createTextNode(`${label} ${valor}`));
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
      celda.textContent = "";

      fila.appendChild(celda);
    }

    tablero.appendChild(fila);
  }
}

function actualizarMarcador(puntuacion) {
  while (marcador.firstChild) marcador.removeChild(marcador.firstChild);
  marcador.appendChild(document.createTextNode(`Punts: ${puntuacion}`));
  actualizarColor(puntuacion);
}

function actualizarColor(puntuacion) {
  marcador.classList.remove("easy", "medium", "hard", "baja", "media", "alta");

  marcador.classList.add(dificultadSeleccionada);

  if (puntuacion >= 500) {
    marcador.classList.add("alta");
  } else if (puntuacion >= 200) {
    marcador.classList.add("media");
  } else {
    marcador.classList.add("baja");
  }
}

function mostrarEstadoFinal(info) {
  estado_juego.innerHTML = "";

  const titulo = document.createElement("h4");
  titulo.appendChild(document.createTextNode(`Partida ${info.estat}`));
  estado_juego.appendChild(titulo);

  const datos = [
    ["Jugador:", info.jugador],
    ["Dificultat:", dificultadSeleccionada],
    ["Puntuació:", info.puntuacio],
    ["Vaixells enfonsats:", `${info.vaixells_enfonsats} / ${info.vaixells_totals}`],
    ["Caselles destapades:", info.caselles_destapades],
    ["Inici:", info.data_inici],
    ["Fi:", info.data_fi]
  ];

  datos.forEach(([label, valor]) => {
    const p = document.createElement("p");
    p.appendChild(document.createTextNode(`${label} ${valor}`));
    estado_juego.appendChild(p);
  });
}