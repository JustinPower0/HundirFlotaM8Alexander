let tabla = document.getElementById("tablero");
let guardar = document.getElementById("guardar");
let estadisticas = document.getElementById("estadisticas");
let estado_juego = document.getElementById("estado_juego");
let partidaID = null;
let intervaloPuntuacion = null;
let dificultadSeleccionada = "medium"; // valor por defecto

const marcador = document.createElement("div");
marcador.setAttribute("id", "puntos");
marcador.textContent = "Punts: 0";
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
      const matriz = data.matriz;
      crearTabla(matriz);

      while (marcador.firstChild) marcador.removeChild(marcador.firstChild);
      const textoInicio = document.createTextNode(`Punts: ${data.puntuacion}`);
      marcador.appendChild(textoInicio);
      actualizarColor(data.puntuacion);

      if (intervaloPuntuacion) clearInterval(intervaloPuntuacion);
      intervaloPuntuacion = setInterval(() => {
        fetch(`http://127.0.0.1:8000/puntuacio_actual/${partidaID}`)
          .then(res => res.json())
          .then(data => {
            while (marcador.firstChild) marcador.removeChild(marcador.firstChild);
            const nuevoTexto = document.createTextNode(`Punts: ${data.puntuacion}`);
            marcador.appendChild(nuevoTexto);
            actualizarColor(data.puntuacion);
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

      while (marcador.firstChild) marcador.removeChild(marcador.firstChild);
      const nuevoTexto = document.createTextNode(`Punts: ${data.puntuacion}`);
      marcador.appendChild(nuevoTexto);
      actualizarColor(data.puntuacion);

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
            estado_juego.innerHTML = `
              <h4>Partida ${info.estat}</h4>
              <p>Jugador: ${info.jugador}</p>
              <p>Dificultat: ${dificultadSeleccionada}</p>
              <p>Puntuació: ${info.puntuacio}</p>
              <p>Vaixells enfonsats: ${info.vaixells_enfonsats} / ${info.vaixells_totals}</p>
              <p>Caselles destapades: ${info.caselles_destapades}</p>
              <p>Inici: ${info.data_inici}</p>
              <p>Fi: ${info.data_fi}</p>
            `;
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
      estado_juego.innerHTML = `
        <h4>Estadístiques globals</h4>
        <p>Total partides: ${data.total_partides}</p>
        <p>Millor puntuació: ${data.millor_puntuacio} (${data.millor_jugador})</p>
        <p>Data millor: ${data.data_millor}</p>
        <h5>Rànquing Top 5:</h5>
        <ol>
          ${data.rànquing_top5.map(p =>
            `<li>${p.jugador} - ${p.puntuacio} punts (${p.files}x${p.columnes})</li>`
          ).join("")}
        </ol>
      `;
    })
    .catch(error => console.error("Error al obtener estadísticas:", error));
});

document.getElementById("ver_estado").addEventListener("click", () => {
  if (!partidaID) return alert("No hi ha partida activa");

  fetch(`http://127.0.0.1:8000/estado_juego/${partidaID}`)
    .then(res => res.json())
    .then(data => {
      estado_juego.innerHTML = `
        <h4>Estat de la partida</h4>
        <p>Jugador: ${data.jugador}</p>
        <p>Estat: ${data.estat}</p>
        <p>Dificultat: ${dificultadSeleccionada}</p>
        <p>Vaixells enfonsats: ${data.vaixells_enfonsats} / ${data.vaixells_totals}</p>
        <p>Caselles destapades: ${data.caselles_destapades}</p>
        <p>Inici: ${data.data_inici}</p>
        <p>Fi: ${data.data_fi || "En curs..."}</p>
      `;
    })
    .catch(error => console.error("Error al obtener estado de juego:", error));
});

document.querySelector(".btn.rojo").addEventListener("click", () => {
  if (!partidaID) return alert("No hi ha partida activa");

  clearInterval(intervaloPuntuacion);
  fetch(`http://127.0.0.1:8000/abandonar/${partidaID}`)
    .then(res => res.json())
    .then(data => {
      estado_juego.innerHTML = `
        <h4>Partida abandonada</h4>
        <p>Jugador: ${data.jugador}</p>
        <p>Estat: ${data.estat}</p>
        <p>Dificultat: ${dificultadSeleccionada}</p>
        <p>Puntuació: ${data.puntuacio}</p>
        <p>Vaixells enfonsats: ${data.vaixells_enfonsats}</p>
        <p>Caselles destapades: ${data.caselles_destapades}</p>
      `;
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

function actualizarColor(puntuacion) {
  if (dificultadSeleccionada === "easy") {
    marcador.style.border = "3px solid #3498db"; // azul
  } else if (dificultadSeleccionada === "hard") {
    marcador.style.border = "3px solid #e67e22"; // naranja
  } else {
    marcador.style.border = "3px solid #95a5a6"; // gris
  }

  if (puntuacion >= 500) {
    marcador.style.backgroundColor = "#2ecc71";
  } else if (puntuacion >= 200) {
    marcador.style.backgroundColor = "#f1c40f";
  } else {
    marcador.style.backgroundColor = "#e74c3c";
  }
}