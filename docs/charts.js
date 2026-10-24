/* Perfect games: grafici in SVG disegnati dai dati JSON inseriti nella pagina (nessuna libreria).
   Ogni grafico ha: linee sottili, un solo colore d'accento, griglia leggera, e un riquadro con i
   valori che compare passando il mouse o toccando lo schermo (e con le frecce della tastiera). */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var C = {
    ink: '#111111', ink2: '#2b2b2b', muted: '#666666', grid: '#ececec', axis: '#c8c8c8',
    context: '#bdbdbd', accent: '#b3261e', wash: 'rgba(179,38,30,0.10)', band: '#f4f4f2', paper: '#ffffff'
  };

  // ---------------------------------------------------------------- formati all'italiana
  function int(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
  function dec(x, d) { return x.toFixed(d).replace('.', ','); }
  function pct(x, d) { return dec(x * 100, d === undefined ? 1 : d) + '%'; }
  function oneIn(s) { return s >= 0.9995 ? 'tutte' : '1 su ' + int(1 / s); }
  function data(id) { var el = document.getElementById(id); return el ? JSON.parse(el.textContent) : null; }

  function svg(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function text(parent, x, y, s, attrs) {
    var a = { x: x, y: y, fill: C.muted, 'font-size': 12 };
    for (var k in attrs) a[k] = attrs[k];
    var t = svg('text', a, parent);
    t.textContent = s;
    return t;
  }
  function html(tag, cls, parent, s) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (s !== undefined) e.textContent = s;
    if (parent) parent.appendChild(e);
    return e;
  }

  // ---------------------------------------------------------------- riquadro dei valori
  function makeTip(host) {
    var tip = html('div', 'tip', host);
    tip.hidden = true;
    return {
      show: function (content, x, y) {
        tip.textContent = '';
        if (content.title) html('div', 't', tip, content.title);
        (content.rows || []).forEach(function (r) {
          var row = html('div', 'r', tip);
          var key = html('i', '', row);
          key.style.borderColor = r.color || 'transparent';
          html('b', '', row, r.value);
          html('span', '', row, r.label || '');
        });
        (content.notes || []).forEach(function (n) { html('div', 't', tip, n); });
        tip.hidden = false;
        var W = host.clientWidth, w = tip.offsetWidth, h = tip.offsetHeight;
        var left = x + 14;
        if (left + w > W) left = x - w - 14;
        if (left < 0) left = Math.max(0, Math.min(W - w, x - w / 2));
        var top = Math.max(0, y - h / 2);
        tip.style.left = left + 'px';
        tip.style.top = top + 'px';
      },
      hide: function () { tip.hidden = true; }
    };
  }

  function onResize(fn) {
    var last = 0, timer;
    window.addEventListener('resize', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        var w = document.documentElement.clientWidth;
        if (w !== last) { last = w; fn(); }
      }, 120);
    });
  }

  // ---------------------------------------------------------------- grafico a linee generico
  // o.x = {min, max, ticks:[...], label}; o.y = {log, min, max, ticks:[{v,label}], label}
  // o.series = [{color, width, points:[{x,y,faded}], markers, hollowFaded, ci:[{x,lo,hi}], area:[{x,lo,hi}]}]
  // o.bands = [x...] (colonne grigie chiare); o.vlines = [{x,label}]; o.hline = {y,label}
  // o.labels = [{x,y,text,dx,dy,anchor,bold}]; o.xs = valori di x su cui si ferma il cursore; o.tip(x) -> contenuto
  function lineChart(plot, o) {
    var host = plot;
    var tip = makeTip(host);
    var cur = null;

    function render() {
      plot.querySelectorAll('svg').forEach(function (s) { s.remove(); });
      tip.hide();
      var W = Math.max(280, plot.clientWidth || 600);
      var narrow = W < 560;
      var H = narrow ? Math.round(W * 0.95) : Math.round(Math.min(460, W * 0.56));
      var m = { t: 18, r: narrow ? 10 : 22, b: o.x.label ? 46 : 28, l: narrow ? o.left[0] : o.left[1] };
      var iw = W - m.l - m.r, ih = H - m.t - m.b;
      var L = Math.log10;
      function sx(v) { return m.l + (v - o.x.min) / (o.x.max - o.x.min) * iw; }
      function sy(v) {
        if (o.y.log) return m.t + (L(o.y.max) - L(Math.max(v, o.y.min))) / (L(o.y.max) - L(o.y.min)) * ih;
        return m.t + (o.y.max - v) / (o.y.max - o.y.min) * ih;
      }
      var s = svg('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': o.aria });
      var step = iw / (o.x.max - o.x.min);

      (o.bands || []).forEach(function (b) {
        svg('rect', { x: sx(b) - step / 2, y: m.t, width: step, height: ih, fill: C.band }, s);
      });
      // griglia e tacche
      o.y.ticks.forEach(function (t) {
        var y = sy(t.v);
        svg('line', { x1: m.l, x2: m.l + iw, y1: y, y2: y, stroke: C.grid, 'stroke-width': 1 }, s);
        text(s, m.l - 8, y + 4, t.label, { 'text-anchor': 'end' });
      });
      svg('line', { x1: m.l, x2: m.l + iw, y1: m.t + ih, y2: m.t + ih, stroke: C.axis, 'stroke-width': 1 }, s);
      var xt = narrow && o.x.ticksNarrow ? o.x.ticksNarrow : o.x.ticks;
      xt.forEach(function (t) {
        svg('line', { x1: sx(t), x2: sx(t), y1: m.t + ih, y2: m.t + ih + 4, stroke: C.axis }, s);
        text(s, sx(t), m.t + ih + 18, String(t), { 'text-anchor': 'middle' });
      });
      if (o.x.label) text(s, m.l + iw / 2, H - 6, narrow && o.x.labelNarrow ? o.x.labelNarrow : o.x.label, { 'text-anchor': 'middle', fill: C.ink2, 'font-size': 12.5 });
      if (o.hline) {
        var hy = sy(o.hline.y);
        svg('line', { x1: m.l, x2: m.l + iw, y1: hy, y2: hy, stroke: C.ink2, 'stroke-width': 1 }, s);
        if (o.hline.label) text(s, m.l + 4, hy + 18, narrow && o.hline.labelNarrow ? o.hline.labelNarrow : o.hline.label, { fill: C.ink2 });
      }
      (o.vlines || []).forEach(function (v) {
        svg('line', { x1: sx(v.x), x2: sx(v.x), y1: m.t, y2: m.t + ih, stroke: C.ink2, 'stroke-width': 1 }, s);
        if (v.label) text(s, sx(v.x) - 6, m.t + 12, narrow && v.labelNarrow ? v.labelNarrow : v.label, { 'text-anchor': 'end', fill: C.ink2 });
      });
      // serie: area (intervallo), barre di errore, linee, punti
      o.series.forEach(function (se) {
        if (se.area) {
          var a = se.area, d = '';
          a.forEach(function (p, i) { d += (i ? 'L' : 'M') + sx(p.x) + ',' + sy(p.hi); });
          for (var i = a.length - 1; i >= 0; i--) d += 'L' + sx(a[i].x) + ',' + sy(a[i].lo);
          svg('path', { d: d + 'Z', fill: se.areaColor || C.wash, stroke: 'none' }, s);
        }
        (se.ci || []).forEach(function (c) {
          svg('line', { x1: sx(c.x), x2: sx(c.x), y1: sy(c.lo), y2: sy(c.hi), stroke: se.color, 'stroke-width': 1.2, 'stroke-opacity': 0.4 }, s);
        });
      });
      o.series.forEach(function (se) {
        var pts = se.points.filter(function (p) { return p.y !== null && p.y !== undefined; });
        var solid = [], faded = [];
        pts.forEach(function (p, i) {
          if (!p.faded) solid.push(p);
          else { if (!faded.length && i > 0) faded.push(pts[i - 1]); faded.push(p); }
        });
        [[solid, 1], [faded, 0.35]].forEach(function (pair) {
          if (pair[0].length < 2) return;
          svg('polyline', {
            points: pair[0].map(function (p) { return sx(p.x) + ',' + sy(p.y); }).join(' '),
            fill: 'none', stroke: se.color, 'stroke-width': se.width || 2, 'stroke-opacity': pair[1] * (se.opacity || 1),
            'stroke-linejoin': 'round', 'stroke-linecap': 'round'
          }, s);
        });
        if (se.markers) pts.forEach(function (p) {
          var hollow = p.faded && se.hollowFaded;
          svg('circle', { cx: sx(p.x), cy: sy(p.y), r: 4, fill: hollow ? C.paper : se.color,
            stroke: hollow ? se.color : C.paper, 'stroke-width': hollow ? 1.5 : 2 }, s);
        });
      });
      (o.dots || []).forEach(function (d) {
        svg('circle', { cx: sx(d.x), cy: sy(d.y), r: 4.5, fill: d.color, stroke: C.paper, 'stroke-width': 2 }, s);
      });
      (o.labels || []).forEach(function (l) {
        if (narrow && l.wide) return;
        text(s, sx(l.x) + (l.dx || 0), sy(l.y) + (l.dy || 0), l.text,
          { 'text-anchor': l.anchor || 'start', fill: C.ink, 'font-size': 12.5, 'font-weight': l.bold ? 650 : 400 });
      });

      // cursore: linea verticale che si aggancia al battitore più vicino
      var cross = svg('line', { y1: m.t, y2: m.t + ih, stroke: C.ink2, 'stroke-width': 1, visibility: 'hidden' }, s);
      var hot = svg('g', {}, s);
      var hit = svg('rect', { x: m.l - step / 2, y: m.t, width: iw + step, height: ih, fill: 'transparent',
        tabindex: 0, 'aria-label': 'Valori del grafico: usa le frecce sinistra e destra' }, s);
      hit.style.cursor = 'crosshair';
      hit.style.outline = 'none';

      function showAt(x) {
        cur = x;
        var X = sx(x);
        cross.setAttribute('x1', X); cross.setAttribute('x2', X); cross.setAttribute('visibility', 'visible');
        hot.textContent = '';
        var c = o.tip(x);
        (c.marks || []).forEach(function (mk) {
          if (mk.y === null || mk.y === undefined) return;
          svg('circle', { cx: X, cy: sy(mk.y), r: 5, fill: mk.color, stroke: C.paper, 'stroke-width': 2 }, hot);
        });
        var ys = (c.marks || []).filter(function (mk) { return mk.y != null; }).map(function (mk) { return sy(mk.y); });
        var y = ys.length ? Math.min.apply(null, ys) : m.t + ih / 2;
        tip.show(c, X, Math.max(m.t + 30, Math.min(y, m.t + ih - 30)));
      }
      function hide() { cross.setAttribute('visibility', 'hidden'); hot.textContent = ''; tip.hide(); }
      function nearest(evt) {
        var r = s.getBoundingClientRect();
        var px = (evt.clientX - r.left) * (W / r.width);
        var v = o.x.min + (px - m.l) / iw * (o.x.max - o.x.min);
        var best = o.xs[0];
        o.xs.forEach(function (x) { if (Math.abs(x - v) < Math.abs(best - v)) best = x; });
        return best;
      }
      hit.addEventListener('pointermove', function (e) { showAt(nearest(e)); });
      hit.addEventListener('pointerdown', function (e) { showAt(nearest(e)); });
      hit.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') hide(); });
      hit.addEventListener('focus', function () { showAt(cur !== null ? cur : o.xs[Math.floor(o.xs.length / 2)]); });
      hit.addEventListener('blur', hide);
      hit.addEventListener('keydown', function (e) {
        var i = o.xs.indexOf(cur);
        if (e.key === 'ArrowRight' && i < o.xs.length - 1) { showAt(o.xs[i + 1]); e.preventDefault(); }
        if (e.key === 'ArrowLeft' && i > 0) { showAt(o.xs[i - 1]); e.preventDefault(); }
        if (e.key === 'Escape') hide();
      });
      plot.insertBefore(s, plot.firstChild);
    }
    render();
    onResize(render);
    document.addEventListener('pointerdown', function (e) { if (!plot.contains(e.target)) tip.hide(); });
    return { render: render };
  }

  // ---------------------------------------------------------------- tabelle "i numeri del grafico"
  function table(parent, head, rows, numFrom) {
    var wrap = html('div', 'table-wrap', parent);
    var t = html('table', '', wrap);
    var tr = html('tr', '', html('thead', '', t));
    head.forEach(function (h, i) { html('th', i >= numFrom ? 'num' : '', tr, h); });
    var tb = html('tbody', '', t);
    rows.forEach(function (r) {
      var row = html('tr', '', tb);
      r.forEach(function (c, i) { html('td', i >= numFrom ? 'num' : '', row, c); });
    });
  }

  var LOG_TICKS = [
    { v: 1, label: 'tutte' }, { v: 0.1, label: '1 su 10' }, { v: 0.01, label: '1 su 100' },
    { v: 0.001, label: '1 su 1.000' }, { v: 0.0001, label: '1 su 10.000' }, { v: 0.00001, label: '1 su 100.000' }
  ];
  function range(a, b) { var r = []; for (var i = a; i <= b; i++) r.push(i); return r; }

  // ---------------------------------------------------------------- 1. La curva
  function curva() {
    var D = data('dati-curva');
    var fig = document.getElementById('grafico-curva');
    if (!D || !fig) return;
    var plot = fig.querySelector('.plot');
    var state = { era: null };
    var all = D.tutte;
    function at(arr, n) { return arr[n] === undefined ? null : arr[n]; }
    var chart;
    function options() {
      var series = D.epoche.map(function (e) {
        return { color: state.era === e.id ? C.ink : C.context, width: state.era === e.id ? 2 : 1.25,
          points: range(0, 27).map(function (n) { return { x: n, y: at(e.s, n) }; }) };
      });
      // l'epoca scelta va disegnata sopra le altre
      series.sort(function (a, b) { return (a.color === C.ink) - (b.color === C.ink); });
      series.push({ color: C.accent, width: 3, points: range(0, 27).map(function (n) { return { x: n, y: all.s[n] }; }) });
      var key = [9, 18, 27];
      return {
        aria: 'Quota di partite ancora perfette dopo ogni battitore, scala logaritmica',
        left: [82, 92],
        x: { min: 0, max: 27, ticks: [0, 3, 6, 9, 12, 15, 18, 21, 24, 27], ticksNarrow: [0, 9, 18, 27],
          label: 'Battitori avversari eliminati di fila', labelNarrow: 'Battitori eliminati di fila' },
        y: { log: true, min: 0.00001, max: 1, ticks: LOG_TICKS },
        vlines: [{ x: 27, label: '27 = perfect game', labelNarrow: 'perfect game' }],
        series: series,
        dots: key.map(function (n) { return { x: n, y: all.s[n], color: C.accent }; }),
        labels: key.map(function (n) { return { x: n, y: all.s[n], text: oneIn(all.s[n]), dx: n === 27 ? -8 : 6, dy: n === 27 ? 20 : -10, anchor: n === 27 ? 'end' : 'start', bold: true }; }),
        xs: range(0, 27),
        tip: function (n) {
          var rows = [{ color: C.accent, value: oneIn(all.s[n]), label: 'tutte le epoche' }];
          var marks = [{ y: all.s[n], color: C.accent }];
          D.epoche.forEach(function (e) {
            var v = at(e.s, n);
            if (state.era && state.era !== e.id) return;
            rows.push({ color: state.era === e.id ? C.ink : C.context, value: v === null ? '—' : oneIn(v), label: e.label });
            if (state.era === e.id && v !== null) marks.push({ y: v, color: C.ink });
          });
          return { title: n === 0 ? 'Prima del primo battitore' : 'Dopo ' + n + (n === 1 ? ' battitore' : ' battitori') + ' eliminati',
            rows: rows, marks: marks,
            notes: ['Squadre ancora in gioco: ' + int(all.r[n])] };
        }
      };
    }
    // pulsanti per evidenziare un'epoca
    var box = fig.querySelector('.eras');
    html('span', '', box, 'Evidenzia un\'epoca:');
    D.epoche.forEach(function (e) {
      var b = html('button', '', box, e.label);
      b.type = 'button';
      b.title = e.nome;
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', function () {
        state.era = state.era === e.id ? null : e.id;
        box.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
        if (state.era) b.setAttribute('aria-pressed', 'true');
        Object.assign(opts, options());
        chart.render();
      });
    });
    var opts = options();
    chart = lineChart(plot, opts);
    // tabella
    var tb = fig.parentNode.querySelector('#numeri-curva .body');
    if (tb) table(tb, ['Battitori', 'Tutte'].concat(D.epoche.map(function (e) { return e.label; })),
      range(1, 27).map(function (n) {
        return [String(n), oneIn(all.s[n])].concat(D.epoche.map(function (e) { var v = at(e.s, n); return v === null ? '—' : oneIn(v); }));
      }), 1);
  }

  // ---------------------------------------------------------------- 2. Come cala
  function comeCala() {
    var D = data('dati-come-cala');
    var fig = document.getElementById('grafico-come-cala');
    if (!D || !fig) return;
    var min = D.min_rischio;
    function pts(arr) { return arr.map(function (p) { return { x: p.n, y: p.h, faded: p.r < min }; }); }
    function ci(arr) { return arr.filter(function (p) { return p.r >= min; }).map(function (p) { return { x: p.n, lo: p.lo, hi: p.hi }; }); }
    var senza = D.senza_dh, con = D.con_dh;
    lineChart(fig.querySelector('.plot'), {
      aria: 'Probabilità di perdere la partita perfetta a ogni battitore, con e senza DH',
      left: [40, 44],
      x: { min: 1, max: 27, ticks: [1, 3, 6, 9, 12, 15, 18, 21, 24, 27],
        ticksNarrow: [1, 9, 18, 27], label: 'Battitore affrontato (tutti i precedenti eliminati)', labelNarrow: 'Battitore affrontato' },
      y: { min: 0, max: 0.5, ticks: [0, 0.1, 0.2, 0.3, 0.4, 0.5].map(function (v) { return { v: v, label: pct(v, 0) }; }) },
      bands: [9, 18, 27],
      series: [
        { color: C.ink2, points: pts(con), ci: ci(con), markers: true, hollowFaded: true },
        { color: C.accent, points: pts(senza), ci: ci(senza), markers: true, hollowFaded: true }
      ],
      labels: [
        { x: 9, y: senza[8].h, text: pct(senza[8].h), dx: -8, dy: 18, anchor: 'end', bold: true },
        { x: 18, y: senza[17].h, text: pct(senza[17].h), dx: -8, dy: 18, anchor: 'end', bold: true, wide: true },
        { x: 27, y: 0.47, text: 'punti vuoti: meno di ' + min + ' squadre', dx: 4, anchor: 'end', wide: true }
      ],
      xs: range(1, 27),
      tip: function (n) {
        var a = senza[n - 1], b = con[n - 1];
        var notes = [];
        if (n % 9 === 0) notes.push('Battitore n. ' + n + ': il nono della formazione');
        if (a.r < min || b.r < min) notes.push('Poche squadre ancora in gioco: dato incerto');
        return { title: 'Battitore n. ' + n,
          rows: [
            { color: C.accent, value: pct(a.h), label: 'senza DH (' + int(a.r) + ' squadre)' },
            { color: C.ink2, value: pct(b.h), label: 'con DH (' + int(b.r) + ' squadre)' }
          ],
          marks: [{ y: a.h, color: C.accent }, { y: b.h, color: C.ink2 }], notes: notes };
      }
    });
    var tb = document.querySelector('#numeri-come-cala .body');
    if (tb) table(tb, ['Battitore', 'Senza DH', 'Squadre a rischio', 'Con DH', 'Squadre a rischio'],
      senza.map(function (a, i) { var b = con[i]; return [String(a.n), pct(a.h), int(a.r), pct(b.h), int(b.r)]; }), 1);
  }

  // ---------------------------------------------------------------- 3. Giornata di grazia
  function grazia() {
    var D = data('dati-grazia');
    var fig = document.getElementById('grafico-grazia');
    if (!D || !fig) return;
    var P = D.punti;
    var lab = [9, 18, 27].map(function (n) { var p = P[n - 1]; return { x: n, y: p.ratio, text: dec(p.ratio, n === 27 ? 1 : 2), dx: n === 27 ? -10 : -6, dy: n === 27 ? 22 : -12, anchor: 'end', bold: true }; });
    lineChart(fig.querySelector('.plot'), {
      aria: 'Rapporto tra partite ancora perfette reali e attese dal modello, battitore per battitore',
      left: [40, 44],
      x: { min: 1, max: 27, ticks: [1, 3, 6, 9, 12, 15, 18, 21, 24, 27], ticksNarrow: [1, 9, 18, 27],
        label: 'Battitori eliminati di fila', labelNarrow: 'Battitori eliminati di fila' },
      y: { min: 0.5, max: 4, ticks: [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4].map(function (v) { return { v: v, label: v === 1 ? '1' : dec(v, v % 1 ? 1 : 0) }; }) },
      hline: { y: 1, label: '1 = come se ogni battitore fosse indipendente', labelNarrow: '1 = come il caso' },
      series: [{ color: C.accent, width: 2.5, points: P.map(function (p) { return { x: p.n, y: p.ratio }; }),
        area: P.map(function (p) { return { x: p.n, lo: p.lo, hi: p.hi }; }) }],
      dots: [9, 18, 27].map(function (n) { return { x: n, y: P[n - 1].ratio, color: C.accent }; }),
      labels: lab,
      xs: range(1, 27),
      tip: function (n) {
        var p = P[n - 1];
        return { title: 'Dopo ' + n + (n === 1 ? ' battitore' : ' battitori') + ' eliminati',
          rows: [
            { color: C.accent, value: dec(p.ratio, 2) + '×', label: 'reale / atteso' },
            { color: null, value: oneIn(p.s), label: 'ancora perfette, reale' },
            { color: null, value: oneIn(p.s0), label: 'attese dal caso' }
          ],
          notes: ['Intervallo al 95%: ' + dec(p.lo, 2) + '–' + dec(p.hi, 2)],
          marks: [{ y: p.ratio, color: C.accent }] };
      }
    });
    var tb = document.querySelector('#numeri-grazia .body');
    if (tb) table(tb, ['Battitori', 'Reale', 'Atteso dal caso', 'Rapporto', 'Intervallo 95%'],
      P.map(function (p) { return [String(p.n), oneIn(p.s), oneIn(p.s0), dec(p.ratio, 2), dec(p.lo, 2) + '–' + dec(p.hi, 2)]; }), 1);
  }

  // ---------------------------------------------------------------- 6. Gli stadi (righe con barre)
  function stadi() {
    var D = data('dati-stadi');
    var box = document.getElementById('grafico-stadi');
    if (!D || !box) return;
    var host = box.querySelector('.plot');
    var tip = makeTip(host);
    var MAX = 0.5;   // scala: da -50% a +50%
    var bars = html('div', 'bars', host);
    var sc = html('div', 'bars-scale', bars);
    html('span', '', sc, 'Stadio');
    var ticks = html('span', 'ticks', sc);
    [-0.4, -0.2, 0, 0.2, 0.4].forEach(function (v) {
      var t = html('span', Math.abs(v) === 0.2 ? 'minor' : '', ticks, v === 0 ? '0' : (v > 0 ? '+' : '−') + Math.abs(v * 100) + '%');
      t.style.left = (50 + v / MAX * 50) + '%';
    });
    html('span', '', sc, '');
    var list = html('div', '', bars);
    list.setAttribute('role', 'list');
    D.stadi.forEach(function (p) {
      var row = html('div', 'bar-row' + (p.evidenza ? ' hl' : ''), list);
      row.setAttribute('role', 'listitem');
      row.tabIndex = 0;
      html('span', 'bar-name', row, p.nome);
      var track = html('span', 'bar-track', row);
      var d = p.ratio - 1;
      var f = html('span', 'bar-fill ' + (d >= 0 ? 'up' : 'down'), track);
      var w = Math.min(Math.abs(d), MAX) / MAX * 50;
      f.style.left = (d >= 0 ? 50 : 50 - w) + '%';
      f.style.width = Math.max(w, 0.6) + '%';
      var pc = Math.round(Math.abs(d) * 100);
      var label = pc === 0 ? '0%' : (d >= 0 ? '+' : '−') + pc + '%';
      html('span', 'bar-val', row, label);
      row.setAttribute('aria-label', p.nome + ', ' + p.citta + ', ' + p.anni + ': ' + label + ' rispetto alle attese');
      function show() {
        var r = row.getBoundingClientRect(), hr = host.getBoundingClientRect();
        tip.show({ title: p.nome + ', ' + p.citta + ' (' + p.anni + ')',
          rows: [
            { color: p.evidenza ? C.accent : C.context, value: label, label: 'rispetto alle attese' },
            { color: null, value: int(p.O), label: 'serie da 9 o più eliminati' },
            { color: null, value: dec(p.E, 0), label: 'attese' }
          ],
          notes: [int(p.n) + ' squadre al lancio'] }, hr.width * 0.45, r.top - hr.top + r.height / 2);
      }
      row.addEventListener('pointerenter', show);
      row.addEventListener('pointerdown', show);
      row.addEventListener('focus', show);
      row.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') tip.hide(); });
      row.addEventListener('blur', function () { tip.hide(); });
    });
    document.addEventListener('pointerdown', function (e) { if (!host.contains(e.target)) tip.hide(); });
  }

  curva();
  comeCala();
  grazia();
  stadi();
})();
