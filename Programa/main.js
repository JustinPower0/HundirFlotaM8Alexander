let tabla = document.getElementById("tabla");


tabla.addEventListener("click", (event) => {
    event.preventDefault();
    let dimencion = parseInt(prompt("Introduzca una fila max 20"))
    let dim = parseInt(prompt("Introduzca una columna max 20"))
    fetch("http://127.0.0.1:8000/barcos/" + dimencion + dim)
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
