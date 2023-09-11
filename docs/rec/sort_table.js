const $$ = {
  q: (query, config = {}) => {
    if (config.scope == null) config.scope = document;
    if (Array.isArray(config.scope)) {
      const cnfg = Object.assign({}, config);
      return config.scope.flatMap(n=>{
        cnfg.scope = n;
        return $$.q(query, cnfg);
      });
    }
    let nodes = Array.from(config.scope.querySelectorAll(query));
    if (config.has!=null) nodes = nodes.filter(n=>n.querySelector(config.has) !=null);
    return nodes;
  },
  column: (th) => {
    if (th == null || th.tagName != 'TH') return null;
    const ths = Array.from(th.closest("tr").querySelectorAll("th"));
    const index=ths.indexOf(th);
    const trs = th.closest("table").querySelectorAll("tbody tr");
    return Array.from(trs).map(tr=>{
      const tds = tr.querySelectorAll("td");
      return tds[index];
    })
  }
}

function mkTableSortable(table) {
  if (table == null || table.tagName != "TABLE") return;
  table.querySelectorAll("thead th.isSortable").forEach(t=>{
    const cls = $$.column(t);
    const dif = [...new Set(cls.map(x=>x.textContent.trim()))];
    if (dif.length<2) {
      t.classList.remove("isSortable");
      if (!t.classList.contains("hideIfEQ")) return;
      cls.concat([t]).forEach(x=>x.style.display='none');
      let cp = table.querySelector("caption");
      if (cp == null) {
          cp = document.createElement("caption");
          table.prepend(cp);
      }
      if (cls[0].textContent.trim().length) {
          if (cp.textContent.trim().length) cp.append(", ");
          cp.append((t.getAttribute("title") || t.textContent)+": ");
          cp.innerHTML += cls[0].innerHTML;
      }
      return;
    }
  })
  const ths = table.querySelectorAll("thead th.isSortable");
  const trs = table.querySelectorAll("tbody tr");
  if (ths.length == 0 || trs.length==0) return;

  const gKey = (isStr, td) => {
    let sortkey = td.getAttribute("data-sortkey");
    if (sortkey == null) {
      sortkey = td.textContent.trim();
      if (isStr) {
        sortkey = sortkey.toLowerCase();
      } else {
        sortkey = Number(sortkey.replace("%", ""));
      }
      td.setAttribute("data-sortkey", sortkey);
    }
    if (!isStr) sortkey = parseFloat(sortkey);
    return sortkey;
  }

  const tbody = table.querySelector("tbody");

  ths.forEach(th=>{
    if (th.title && th.title.trim().length) {
      th.title = th.title + " (haz click para ordenar)";
    } else {
      th.title = "Haz click para ordenar";
    }
    const isStr = th.classList.contains("str");
    const tds = $$.column(th);
    const ord = tds.map((td, index)=>{
      const t = td.textContent.trim().toLowerCase();
      const k = gKey(isStr, td);
      return [index, k, t];
    }).sort((a, b) => {
      let ka = a[1];
      let kb = b[1];
      if (isStr) return ka.localeCompare(kb);
      if (isNaN(ka) && isNaN(kb)) return a[2].localeCompare(b[2]);
      if (isNaN(ka)) ka = Infinity;
      if (isNaN(kb)) kb = Infinity;
      return ka - kb;
    }).map(i => i[0]);
    th.addEventListener("click", () => {
      const doReversed = th.classList.contains("isSortedByMe") && !th.classList.contains("isReversed");
      th.closest("tr").querySelectorAll("th").forEach(x=>{
        x.classList.remove("isSortedByMe", "isReversed");
      });
      th.classList.add("isSortedByMe");
      let order = ord;
      if (doReversed) order = order.slice().reverse();
      order.forEach(o => {
        tbody.append(trs[o]);
      });
      if (doReversed) {
        th.classList.add("isReversed");
      } else {
        th.classList.remove("isReversed");
      }
      let count = 0;
      table.querySelectorAll("tbody tr").forEach(tr=>{
        if (tr.style.display=='') {
          count++;
          tr.classList.remove(count%2==0?"odd":"even");
          tr.classList.add(count%2==0?"even":"odd");
        }
      })
    })
  })
}

document.addEventListener("DOMContentLoaded", function() {
  $$.q("table", {
    has: ".isSortable"
  }).map(mkTableSortable);
});