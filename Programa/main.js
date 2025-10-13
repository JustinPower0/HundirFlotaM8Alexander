let tabla = document.getElementById("tablero");


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


let celdas = ""
let dimX = 6, dimY = 5;

for (let i = 0; i < dimX; i++) {
    celdas += "<tr>"
    for (let j = 0; j < dimY; j++) {
        celdas += "<td id=" + i + j + ">*</td>"
    }
    celdas += "</tr>"
}
document.getElementById("tablero").innerHTML = celdas;

for (let i = 0; i < dimX; i++) {
    for (let j = 0; j < dimY; j++) {
        document.getElementById(i + "" + j).addEventListener("click", (event) => {
            event.target.innerHTML = 1;

            fetch()
        });
    }
}

//pedir al usuario para hacer  la matrix fila columna y nombre usuario
//para hacer la peticion es con get 

