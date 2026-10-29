/* Perfect games: grafici in SVG disegnati dai dati JSON inseriti nella pagina (nessuna libreria).
   Ogni grafico ha: linee sottili, un solo colore d'accento, griglia leggera, e un riquadro con i
   valori che compare passando il mouse o toccando lo schermo (e con le frecce della tastiera). */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var C = {
    // tabellone: bianco per il dato principale, giallo per l'evidenza, verdi spenti per il contesto
    ink: '#f4f6f1', ink2: '#dfe9e2', muted: '#9fbfac', grid: '#0b2017', axis: '#6f9a82',
    context: '#7fae93', accent: '#ffd21f', wash: 'rgba(244,246,241,0.12)', band: 'rgba(11,32,23,0.45)',
    paper: '#163c29', slot: '#0b2017'
  };

  // ---------------------------------------------------------------- formati all'inglese (17,457 e 28.6%)
  function int(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function dec(x, d) { return x.toFixed(d); }
  function pct(x, d) { return dec(x * 100, d === undefined ? 1 : d) + '%'; }
  function oneIn(s) { return s >= 0.9995 ? 'all' : '1 in ' + int(1 / s); }
  function data(id) { var el = document.getElementById(id); return el ? JSON.parse(el.textContent) : null; }

  function svg(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function text(parent, x, y, s, attrs) {
    var a = { x: x, y: y, fill: C.muted, 'font-size': 15 };
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
        svg('line', { x1: m.l, x2: m.l + iw, y1: y, y2: y, stroke: C.grid, 'stroke-width': 1.5 }, s);
        text(s, m.l - 8, y + 4, t.label, { 'text-anchor': 'end' });
      });
      svg('line', { x1: m.l, x2: m.l + iw, y1: m.t + ih, y2: m.t + ih, stroke: C.axis, 'stroke-width': 2 }, s);
      var xt = narrow && o.x.ticksNarrow ? o.x.ticksNarrow : o.x.ticks;
      xt.forEach(function (t) {
        svg('line', { x1: sx(t), x2: sx(t), y1: m.t + ih, y2: m.t + ih + 4, stroke: C.axis }, s);
        text(s, sx(t), m.t + ih + 21, String(t), { 'text-anchor': 'middle', fill: C.ink2, 'font-size': 16 });
      });
      if (o.x.label) text(s, m.l + iw / 2, H - 6, narrow && o.x.labelNarrow ? o.x.labelNarrow : o.x.label, { 'text-anchor': 'middle', fill: C.muted, 'font-size': 15, 'letter-spacing': '0.06em' });
      if (o.hline) {
        var hy = sy(o.hline.y);
        svg('line', { x1: m.l, x2: m.l + iw, y1: hy, y2: hy, stroke: C.muted, 'stroke-width': 1.5, 'stroke-dasharray': '6 4' }, s);
        if (o.hline.label) text(s, m.l + 6, hy + 20, narrow && o.hline.labelNarrow ? o.hline.labelNarrow : o.hline.label, { fill: C.ink2 });
      }
      (o.vlines || []).forEach(function (v) {
        svg('line', { x1: sx(v.x), x2: sx(v.x), y1: m.t, y2: m.t + ih, stroke: C.muted, 'stroke-width': 1.5 }, s);
        if (v.label) text(s, sx(v.x) - 8, m.t + 14, narrow && v.labelNarrow ? v.labelNarrow : v.label, { 'text-anchor': 'end', fill: C.ink2 });
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
          svg('rect', { x: sx(p.x) - 4, y: sy(p.y) - 4, width: 8, height: 8, fill: hollow ? C.paper : se.color,
            stroke: hollow ? se.color : C.paper, 'stroke-width': hollow ? 1.5 : 2 }, s);
        });
      });
      (o.dots || []).forEach(function (d) {
        svg('rect', { x: sx(d.x) - 7, y: sy(d.y) - 7, width: 14, height: 14, fill: d.color, stroke: C.slot, 'stroke-width': 2 }, s);
      });
      // le etichette in grassetto stanno in una feritoia nera con cifre gialle (misurate dopo, a svg in pagina)
      var slotted = [];
      (o.labels || []).forEach(function (l) {
        if (narrow && l.wide) return;
        var lt = text(s, sx(l.x) + (l.dx || 0), sy(l.y) + (l.dy || 0), l.text,
          { 'text-anchor': l.anchor || 'start', fill: l.bold ? C.accent : C.ink2, 'font-size': l.bold ? 20 : 15, 'font-weight': l.bold ? 900 : 700 });
        if (l.bold) slotted.push(lt);
      });

      // cursore: linea verticale che si aggancia al battitore più vicino
      var cross = svg('line', { y1: m.t, y2: m.t + ih, stroke: C.muted, 'stroke-width': 1.5, visibility: 'hidden' }, s);
      var hot = svg('g', {}, s);
      var hit = svg('rect', { x: m.l - step / 2, y: m.t, width: iw + step, height: ih, fill: 'transparent',
        tabindex: 0, 'aria-label': 'Chart values: use the left and right arrow keys' }, s);
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
          svg('rect', { x: X - 6, y: sy(mk.y) - 6, width: 12, height: 12, fill: mk.color, stroke: C.slot, 'stroke-width': 2 }, hot);
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
      slotted.forEach(function (lt) {
        var b = lt.getBBox();
        s.insertBefore(svg('rect', { x: b.x - 6, y: b.y - 1, width: b.width + 12, height: b.height + 2, fill: C.slot }), lt);
      });
    }
    render();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(render);
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
    { v: 1, label: 'all' }, { v: 0.1, label: '1 in 10' }, { v: 0.01, label: '1 in 100' },
    { v: 0.001, label: '1 in 1,000' }, { v: 0.0001, label: '1 in 10,000' }, { v: 0.00001, label: '1 in 100,000' }
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
        return { color: state.era === e.id ? C.accent : C.context, width: state.era === e.id ? 3 : 1.5, opacity: state.era === e.id ? 1 : 0.75,
          points: range(0, 27).map(function (n) { return { x: n, y: at(e.s, n) }; }) };
      });
      // l'epoca scelta va disegnata sopra le altre
      series.sort(function (a, b) { return (a.color === C.accent) - (b.color === C.accent); });
      series.push({ color: C.ink, width: 4.5, points: range(0, 27).map(function (n) { return { x: n, y: all.s[n] }; }) });
      var key = [9, 18, 27];
      return {
        aria: 'Share of games still perfect after each batter, log scale',
        left: [82, 92],
        x: { min: 0, max: 27, ticks: [0, 3, 6, 9, 12, 15, 18, 21, 24, 27], ticksNarrow: [0, 9, 18, 27],
          label: 'Opposing batters retired in a row', labelNarrow: 'Batters retired in a row' },
        y: { log: true, min: 0.00001, max: 1, ticks: LOG_TICKS },
        vlines: [{ x: 27, label: '27 = perfect game', labelNarrow: 'perfect game' }],
        series: series,
        dots: key.map(function (n) { return { x: n, y: all.s[n], color: C.accent }; }),
        labels: key.map(function (n) { return { x: n, y: all.s[n], text: oneIn(all.s[n]), dx: n === 27 ? -8 : 6, dy: n === 27 ? 20 : -10, anchor: n === 27 ? 'end' : 'start', bold: true }; }),
        xs: range(0, 27),
        tip: function (n) {
          var rows = [{ color: C.ink, value: oneIn(all.s[n]), label: 'all eras' }];
          var marks = [{ y: all.s[n], color: C.ink }];
          D.epoche.forEach(function (e) {
            var v = at(e.s, n);
            if (state.era && state.era !== e.id) return;
            rows.push({ color: state.era === e.id ? C.accent : C.context, value: v === null ? '—' : oneIn(v), label: e.label });
            if (state.era === e.id && v !== null) marks.push({ y: v, color: C.accent });
          });
          return { title: n === 0 ? 'Before the first batter' : 'After ' + n + (n === 1 ? ' batter' : ' batters') + ' retired',
            rows: rows, marks: marks,
            notes: ['Sides still in play: ' + int(all.r[n])] };
        }
      };
    }
    // pulsanti per evidenziare un'epoca
    var box = fig.querySelector('.eras');
    html('span', '', box, 'Highlight an era:');
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
    if (tb) table(tb, ['Batters', 'All'].concat(D.epoche.map(function (e) { return e.label; })),
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
      aria: 'Chance of losing the perfect game at each batter, with and without a DH',
      left: [40, 44],
      x: { min: 1, max: 27, ticks: [1, 3, 6, 9, 12, 15, 18, 21, 24, 27],
        ticksNarrow: [1, 9, 18, 27], label: 'Batter faced (everyone before him retired)', labelNarrow: 'Batter faced' },
      y: { min: 0, max: 0.5, ticks: [0, 0.1, 0.2, 0.3, 0.4, 0.5].map(function (v) { return { v: v, label: pct(v, 0) }; }) },
      bands: [9, 18, 27],
      series: [
        { color: C.ink, points: pts(con), ci: ci(con), markers: true, hollowFaded: true },
        { color: C.accent, points: pts(senza), ci: ci(senza), markers: true, hollowFaded: true }
      ],
      labels: [
        { x: 9, y: senza[8].h, text: pct(senza[8].h), dx: -8, dy: 18, anchor: 'end', bold: true },
        { x: 18, y: senza[17].h, text: pct(senza[17].h), dx: -8, dy: 18, anchor: 'end', bold: true, wide: true },
        { x: 27, y: 0.47, text: 'hollow points: fewer than ' + min + ' sides', dx: 4, anchor: 'end', wide: true }
      ],
      xs: range(1, 27),
      tip: function (n) {
        var a = senza[n - 1], b = con[n - 1];
        var notes = [];
        if (n % 9 === 0) notes.push('Batter ' + n + ': the No. 9 spot in the lineup');
        if (a.r < min || b.r < min) notes.push('Few sides still in play: shaky number');
        return { title: 'Batter ' + n,
          rows: [
            { color: C.accent, value: pct(a.h), label: 'no DH (' + int(a.r) + ' sides)' },
            { color: C.ink, value: pct(b.h), label: 'with DH (' + int(b.r) + ' sides)' }
          ],
          marks: [{ y: a.h, color: C.accent }, { y: b.h, color: C.ink }], notes: notes };
      }
    });
    var tb = document.querySelector('#numeri-come-cala .body');
    if (tb) table(tb, ['Batter', 'No DH', 'Sides at risk', 'With DH', 'Sides at risk'],
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
      aria: 'Ratio of games actually still perfect to games expected by the model, batter by batter',
      left: [40, 44],
      x: { min: 1, max: 27, ticks: [1, 3, 6, 9, 12, 15, 18, 21, 24, 27], ticksNarrow: [1, 9, 18, 27],
        label: 'Batters retired in a row', labelNarrow: 'Batters retired in a row' },
      y: { min: 0.5, max: 4, ticks: [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4].map(function (v) { return { v: v, label: v === 1 ? '1' : dec(v, v % 1 ? 1 : 0) }; }) },
      hline: { y: 1, label: '1 = as if every batter were independent', labelNarrow: '1 = pure chance' },
      series: [{ color: C.ink, width: 3, points: P.map(function (p) { return { x: p.n, y: p.ratio }; }),
        area: P.map(function (p) { return { x: p.n, lo: p.lo, hi: p.hi }; }) }],
      dots: [9, 18, 27].map(function (n) { return { x: n, y: P[n - 1].ratio, color: C.accent }; }),
      labels: lab,
      xs: range(1, 27),
      tip: function (n) {
        var p = P[n - 1];
        return { title: 'After ' + n + (n === 1 ? ' batter' : ' batters') + ' retired',
          rows: [
            { color: C.ink, value: dec(p.ratio, 2) + '×', label: 'actual / expected' },
            { color: null, value: oneIn(p.s), label: 'still perfect, actual' },
            { color: null, value: oneIn(p.s0), label: 'expected by chance' }
          ],
          notes: ['95% interval: ' + dec(p.lo, 2) + '–' + dec(p.hi, 2)],
          marks: [{ y: p.ratio, color: C.ink }] };
      }
    });
    var tb = document.querySelector('#numeri-grazia .body');
    if (tb) table(tb, ['Batters', 'Actual', 'Expected by chance', 'Ratio', '95% interval'],
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
    html('span', '', sc, 'Ballpark');
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
      row.setAttribute('aria-label', p.nome + ', ' + p.citta + ', ' + p.anni + ': ' + label + ' compared with expected');
      function show() {
        var r = row.getBoundingClientRect(), hr = host.getBoundingClientRect();
        tip.show({ title: p.nome + ', ' + p.citta + ' (' + p.anni + ')',
          rows: [
            { color: p.evidenza ? C.accent : C.context, value: label, label: 'compared with expected' },
            { color: null, value: int(p.O), label: 'starts with 9+ straight outs' },
            { color: null, value: dec(p.E, 0), label: 'expected' }
          ],
          notes: [int(p.n) + ' pitching sides'] }, hr.width * 0.45, r.top - hr.top + r.height / 2);
      }
      row.addEventListener('pointerenter', show);
      row.addEventListener('pointerdown', show);
      row.addEventListener('focus', show);
      row.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') tip.hide(); });
      row.addEventListener('blur', function () { tip.hide(); });
    });
    document.addEventListener('pointerdown', function (e) { if (!host.contains(e.target)) tip.hide(); });
  }

  // ---------------------------------------------------------------- 7. Torture test (righe con intervalli)
  // Per ogni ipotesi due segmenti: stagioni pari (scoperta, punto vuoto) e dispari (conferma, punto pieno).
  // Scala logaritmica del rapporto di probabilita'; i valori fuori scala si fermano al bordo con una freccia.
  function tortura() {
    var D = data('dati-tortura');
    var box = document.getElementById('grafico-tortura');
    if (!D || !box) return;
    var host = box.querySelector('.plot');
    var tip = makeTip(host);
    var LO = 0.7, HI = 1 / 0.7, L = Math.log;
    function pos(v) { return (L(Math.min(Math.max(v, LO), HI)) - L(LO)) / (L(HI) - L(LO)) * 100; }
    var GROUPS = [
      ['new', 'New findings that held up'],
      ['known', 'Known effects that came back (sanity checks)'],
      ['fooled', 'Looked real, wasn’t'],
      ['failed', 'Tried and failed']
    ];
    var FAIL = '#6f9a82';
    function color(h) { return h.gruppo === 'new' ? C.accent : (h.regge ? C.ink : FAIL); }
    function pv(p) { return p < 0.001 ? '<0.001' : (p < 0.01 ? p.toFixed(3) : p.toFixed(2)); }
    function or(x) { return dec(x.OR, 2) + ' (' + dec(x.lo, 2) + '–' + dec(x.hi, 2) + ')'; }

    var wrap = html('div', 'forest', host);
    var sc = html('div', 'forest-scale', wrap);
    html('span', '', sc, '');
    var ticks = html('span', 'ticks', sc);
    [[0.75, '0.75'], [0.9, '0.9'], [1, '1'], [1.1, '1.1'], [1.33, '1.33']].forEach(function (t) {
      var e = html('span', t[0] === 1 ? 'one' : '', ticks, t[1]);
      e.style.left = pos(t[0]) + '%';
    });
    html('span', 'forest-off', sc, 'off scale');
    GROUPS.forEach(function (g) {
      var hs = D.ipotesi.filter(function (h) { return h.gruppo === g[0]; });
      if (!hs.length) return;
      html('div', 'forest-group', wrap, g[1]);
      var list = html('div', '', wrap);
      list.setAttribute('role', 'list');
      hs.forEach(function (h) {
        var col = color(h);
        var row = html('div', 'forest-row', list);
        row.setAttribute('role', 'listitem');
        row.tabIndex = 0;
        row.setAttribute('aria-label', h.nome + '. Even seasons ' + or(h.pari) + ', odd seasons ' + or(h.dispari) +
          (h.regge ? '. Passed the rule.' : '. Did not pass.'));
        html('span', 'forest-name', row, h.nome);
        var track = html('span', 'forest-track', row);
        html('span', 'ref', track).style.left = pos(1) + '%';
        var off = [];
        [[h.pari, 'even', 7, '○'], [h.dispari, 'odd', 19, '●']].forEach(function (k) {
          var x = k[0], y = k[2];
          var a = pos(x.lo), b = pos(x.hi);
          var ci = html('span', 'ci', track);
          ci.style.left = a + '%'; ci.style.width = Math.max(b - a, 0.4) + '%'; ci.style.top = y + 'px';
          ci.style.borderColor = col;
          if (x.lo < LO) { var la = html('span', 'clip left', track); la.style.top = y + 'px'; la.style.borderRightColor = col; }
          if (x.hi > HI) { var ra = html('span', 'clip right', track); ra.style.top = y + 'px'; ra.style.borderLeftColor = col; }
          // punto fuori scala: niente punto, solo la freccia; il valore va nella colonna a destra
          if (x.OR > HI || x.OR < LO) { off.push(k[3] + dec(x.OR, 1)); return; }
          var pt = html('span', 'pt ' + k[1], track);
          pt.style.left = pos(x.OR) + '%'; pt.style.top = y + 'px';
          pt.style.borderColor = col;
          if (k[1] === 'odd') pt.style.background = col;
        });
        html('span', 'forest-off', row, off.join(' '));
        function show() {
          var r = row.getBoundingClientRect(), hr = host.getBoundingClientRect();
          tip.show({ title: h.nome,
            rows: [
              { color: col, value: or(h.pari), label: 'even seasons, p ' + pv(h.pari.p) },
              { color: col, value: or(h.dispari), label: 'odd seasons, p ' + pv(h.dispari.p) }
            ],
            notes: [h.regge ? 'Passed: same direction, p < 0.05 in both halves' : 'Did not pass the rule'] },
            hr.width * 0.4, r.top - hr.top + r.height / 2);
        }
        row.addEventListener('pointerenter', show);
        row.addEventListener('pointerdown', show);
        row.addEventListener('focus', show);
        row.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') tip.hide(); });
        row.addEventListener('blur', function () { tip.hide(); });
      });
    });
    document.addEventListener('pointerdown', function (e) { if (!host.contains(e.target)) tip.hide(); });

    var tb = document.querySelector('#numeri-tortura .body');
    if (tb) table(tb, ['Hypothesis', 'Even seasons', 'p', 'Odd seasons', 'p', 'Passed'],
      D.ipotesi.map(function (h) {
        return [h.nome, or(h.pari), pv(h.pari.p), or(h.dispari), pv(h.dispari.p), h.regge ? 'yes' : 'no'];
      }), 1);
  }

  // ---------------------------------------------------------------- 0. Il tabellone dei 27 battitori (home)
  function lineScore() {
    var D = data('dati-curva');
    var box = document.getElementById('line-score');
    if (!D || !box) return;
    var s = D.tutte.s;
    function f(v) { return v < 10 ? dec(v, 1) : int(v); }
    var h = '<div class="corner">Inning</div>';
    for (var i = 1; i <= 9; i++) h += '<div class="hd" style="--hc:' + (i + 1) + ';--pr2:' + (i + 1) + '">' + i + '</div>';
    ['1st', '2nd', '3rd'].forEach(function (r, k) {
      h += '<div class="rl" style="--rr:' + (k + 2) + ';--pc2:' + (k + 2) + '"><b>' + r + '</b>up</div>';
    });
    for (i = 1; i <= 9; i++) for (var b = 1; b <= 3; b++) {
      var n = (i - 1) * 3 + b;
      h += '<div class="c' + (n % 9 === 0 ? ' hi' : '') + '" style="--dc:' + (i + 1) + ';--dr:' + (b + 1) + ';--pc:' + (b + 1) + ';--pr:' + (i + 1) +
        '" aria-label="After ' + n + ' batters: 1 in ' + f(1 / s[n]) + '"><i>' + n + '</i>' + f(1 / s[n]) + '</div>';
    }
    box.innerHTML = h;
  }

  lineScore();
  curva();
  comeCala();
  grazia();
  stadi();
  tortura();
})();
