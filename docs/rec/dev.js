document.addEventListener("DOMContentLoaded", function() {
    if (document.location.protocol!="file:") return;
    Array.from(document.getElementsByTagName("a")).forEach(a=> {
        if (a.pathname.endsWith("/")) {
            a.pathname = a.pathname + "index.html"
            return;
        }
        if (a.pathname.match(/.*\/(sia|alq)\/\d+$/)) {
            a.pathname = a.pathname + ".html"
            return;
        }
    });
});