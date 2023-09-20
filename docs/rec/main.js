function filtrar() {
    const zdom = document.getElementById("zona");
    const zona = zdom.value.trim();
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
    });
    if (trs.length == count) {
        document.title = "Pisos en Madrid";
    } else {
        document.title = "Pisos en "+zdom.selectedOptions[0].getAttribute("data-label");
    }
    if (zona.length==0 && document.location.search.length<2) return;
    if (zona.length>0 && document.location.search=='?'+zona) return;
    const url = document.location.href.replace(/\?.*$/,"");
    if (zona.length==0) {
        console.log(document.location.href, "->", url);
        history.pushState({}, "", url);
        return;
    }
    console.log(document.location.href, "->", url+'?'+zona);
    history.pushState(zona, "", url+'?'+zona);
}

document.addEventListener("DOMContentLoaded", function() {
    const value = document.location.search.substring(1);
    const zona = document.getElementById("zona");
    if (zona.querySelector("option[value='"+value+"']")==null) {
        const url = document.location.href.replace(/\?.*$/,"");
        console.log(document.location.href, "=>", url);
        history.replaceState({}, "", url);
        zona.value = "";
    }
    else zona.value = value;
    zona.addEventListener("change", filtrar)
    filtrar();
});