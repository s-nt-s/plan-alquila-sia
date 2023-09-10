function filtrar() {
    const zona = document.getElementById("zona").value.trim();
    const trs = document.querySelectorAll("tr[data-zona]");
    trs.forEach(tr=>{
        if (zona.length==0 || zona==tr.getAttribute("data-zona")) tr.style.display = '';
        else tr.style.display = 'none';
    })
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("zona").addEventListener("change", filtrar)
    filtrar();
});