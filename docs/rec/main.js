
const HOME_URL = document.location.href.replace(/\?.*$/,"");

const gAll = (slc) => Array.from(document.querySelectorAll(slc));
const gInt = (s) => {
    const n = parseInt(s, 10);
    return isNaN(n)?null:n;
}
const gStr = (s) => {
    if (s==null) return null;
    s = s.trim();
    return s.length==0?null:s;
}


function hideTr(params, tr) {
    if (params.zona && params.zona!=tr.getAttribute("data-zona")) return true;
    if (params.precio && params.precio<gInt(tr.getAttribute("data-precio"))) return true;
    const tags = tr.querySelector("td.tags").textContent.trim().split(/\s+/);
    for (let i=0; i<params.tags.length; i++) {
        if (!tags.includes(params.tags[i])) return true;
    }
    return false;
}

function filtrar() {
    const precio = gInt(document.getElementById("precio").value, 10);
    const tags = gAll("input[id][type='checkbox']:checked").map((i)=> i.value);
    const zdom = document.getElementById("zona");
    const zona = gStr(zdom.value);
    const trs = document.querySelectorAll("tr[data-zona]");
    const params = {
        zona: zona,
        precio: precio,
        tags: tags
    };
    let count = 0;
    trs.forEach(tr=>{
        if (hideTr(params, tr)) tr.style.display = 'none';
        else {
            count++;
            tr.style.display = '';
            tr.classList.remove(count%2==0?"odd":"even");
            tr.classList.add(count%2==0?"even":"odd");
        }
    });
    if (trs.length == count) {
        document.title = "Pisos en Madrid";
    } else {
        let title = ["Pisos"];
        if (params.zona) {
            title.push("en "+zdom.selectedOptions[0].getAttribute("data-label"));
        } else {
            title.push("en Madrid")
        }
        if (params.precio) {
            title.push("por menos de "+params.precio+"€");
        }
        title = title.concat(params.tags);
        document.title = title.join(" ");
    }
    setQuery(params);
}

function getQuery() {
    if (document.location.search==null) return {tags:[]};
    if (document.location.search.length<2) return {tags:[]};
    const tags = gAll("input[id][type='checkbox']").map((i)=> i.value);
    const query = {
        tags: []
    };
    document.location.search.substring(1).split("&").forEach(v=>{
        v = decodeURIComponent(v).trim();
        if (v.length==0) return;
        const n = gInt(v);
        if (n!=null) {
            query.precio = n;
            return;
        }
        if (document.querySelectorAll("#zona option[value='"+v+"']").length) {
            query.zona = v;
            return;
        }
        if (tags.includes(v) && !query.tags.includes(v)) query.tags.push(v)
    });
    query.tags.sort((a, b) => (tags.indexOf(b) < tags.indexOf(a))?1:-1);
    console.log(query);
    return query;
}


function setQuery(query) {
    let search = [];
    if (query.zona) search.push(query.zona);
    if (query.precio) search.push(query.precio);
    if (query.tags.length) search = search.concat(query.tags);
    const new_search = search.join("&");
    const new_url = new_search.length==0?HOME_URL:(HOME_URL+'?'+new_search);
    if (new_url != document.location.href) {
        console.log(document.location.href, "=>", new_url);
        history.replaceState({}, "", new_url);
    }
}

document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("input[id][type='checkbox']").forEach(i=>{
        const v = document.querySelector('label[for="'+i.id+'"]').textContent.trim();
        i.value = v;
    })
    const query = getQuery();
    setQuery(query);

    const precio = document.getElementById("precio");
    const precios = gAll("tr[data-precio]").map(i=>gInt(i.getAttribute("data-precio"))).concat([
        query.precio,
        gInt(precio.value)
    ]).flatMap(n=>n==null||isNaN(n)||n<0?[]:n);
    if (precios.length) {
        precio.min = Math.min(...precios);
        precio.max = Math.max(...precios);
        if (query.precio) precio.value = query.precio;
    }
    document.getElementById("zona").value = query.zona??"";
    document.getElementById("precio").value = query.precio??"";
    gAll("input[id][type='checkbox']").forEach(i=>{
        i.checked = query.tags.includes(i.value)
    });
    document.querySelectorAll("select[id], input[id]").forEach(n=>{
        n.addEventListener("change", filtrar);
    })
    filtrar();
});