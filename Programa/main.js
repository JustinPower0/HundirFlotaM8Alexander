let tabla = document.getElementById("tablero");
let guardar = document.getElementById("guardar");


tabla.addEventListener("click", (event) => {
    event.preventDefault();
    let dimencion = parseInt(prompt("Introduzca una dimencion max 7"))
    fetch("http://127.0.0.1:8000/barcos/" + dimencion)
        .then(response => response.json())
        .then(data => {
            console.table(data);
        })
        .catch(error => console.error('Error:', error));
    // if (isNaN(dimencion) || dimencion < 7 || dimencion > 20) {
    //     alert("Introduce una dimencion entre 20 y 7")
    // } else {
    // }
})


function crearTabla(matriz) {
    const tbody = document.getElementById("#tablero tbody");
    tbody.innerHTML = "";
    let celdas = ""
    let dimX = 6, dimY = 5;

    for (let i = 0; i < matriz.length; i++) {
        const fila = document.createElement("tr");
        for (let j = 0; j < matriz[i].length; j++) {
            const celda = document.createElement("td");
            celda.setAttribute(i);
            celda.setAttribute(j);
            fila.appendChild(celda);
        }
        tbody.appendChild(fila);
    }
    document.getElementById("tablero").innerHTML = celdas;
 }


 addEventListener("click", (event) => {
     event.preventDefault();
 });