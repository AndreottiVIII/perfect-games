// Testata sempre in alto: scendendo si stringe; --head-h serve agli elementi
// che restano attaccati sotto di lei (la scala del grafico in Torture test).
(function () {
  var root = document.documentElement, head = document.querySelector('header.top');
  if (!head) return;
  function measure() { root.style.setProperty('--head-h', head.offsetHeight + 'px'); }
  function onScroll() {
    var c = window.scrollY > 60;
    if (c !== root.classList.contains('compact')) { root.classList.toggle('compact', c); setTimeout(measure, 200); if (c) showCurrent(); }
  }
  // sul telefono il menu stretto scorre di lato: porta in vista la pagina attuale
  function showCurrent() {
    var nav = head.querySelector('nav'), cur = nav && nav.querySelector('[aria-current]');
    if (cur && nav.scrollWidth > nav.clientWidth) nav.scrollLeft = cur.offsetLeft - (nav.clientWidth - cur.offsetWidth) / 2;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', measure);
  onScroll(); measure();
})();
