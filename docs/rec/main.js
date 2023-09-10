function filtrar() {
    const trs = document.querySelectorAll("tr[data-zona]");
    const show = Array.from(document.querySelectorAll("#zonas input")).filter(i=>i.checked).map(i=>i.value);
    if (show.length==0) {
        trs.forEach(tr=>{
            tr.style.display = '';
        })
        return;
    }
    trs.forEach(tr=>{
        if (show.includes(tr.getAttribute("data-zona"))) tr.style.display = '';
        else tr.style.display = 'none';
    })
}

document.addEventListener("DOMContentLoaded", function() {
    const npt = document.querySelectorAll("#zonas input");
    if (npt.length==0) return;
    document.querySelectorAll("#zonas input").forEach(i=> {
        i.addEventListener("click", filtrar)
    })
    filtrar();
});