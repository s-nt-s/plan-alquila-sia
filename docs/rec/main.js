function filtrar() {
    const zona = document.getElementById("zona").value.trim();
    const trs = document.querySelectorAll("tr[data-zona]");
    let count = 0;
    trs.forEach(tr=>{
        if (zona.length==0 || zona==tr.getAttribute("data-zona")) {
            count++;
            tr.style.display = '';
            tr.classList.remove(count%2==0?"odd":"even");
            tr.classList.add(count%2==0?"even":"odd");
        }
        else tr.style.display = 'none';
    })
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("zona").addEventListener("change", filtrar)
    filtrar();
});