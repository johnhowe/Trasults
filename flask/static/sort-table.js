(function () {
  var SCORE_COLS = ['D', 'ToF', 'DT', 'H', 'E', 'Total'];

  function parseVal(text) {
    var s = text.trim();
    var n = parseFloat(s.replace(/[^\d.\-]/g, ''));
    return isNaN(n) ? s.toLowerCase() : n;
  }

  function percentile(sorted, p) {
    if (sorted.length === 0) return 0;
    var idx = (p / 100) * (sorted.length - 1);
    var lo = Math.floor(idx);
    var hi = Math.ceil(idx);
    return sorted[lo] + (idx - lo) * (sorted[hi] - sorted[lo]);
  }

  // Higher score = greener  (mirrors the deduction heatmap in reverse)
  // 0.0 → rgb(255,  80,  80)  light red
  // 0.5 → rgb(255, 220,   0)  amber
  // 1.0 → rgb(144, 238, 144)  light green
  function scoreColor(ratio) {
    ratio = Math.max(0, Math.min(1, ratio));
    var r, g, b;
    if (ratio >= 0.5) {
      var t = (ratio - 0.5) / 0.5;
      r = Math.round(255 + t * (144 - 255));
      g = Math.round(220 + t * (238 - 220));
      b = Math.round(t * 144);
    } else {
      var t = ratio / 0.5;
      r = 255;
      g = Math.round(190 + t * (220 - 190));
      b = Math.round(190 * (1 - t));
    }
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }

  function applyScoreColors(table) {
    var headers = Array.from(table.querySelectorAll('thead th'));
    headers.forEach(function (th, idx) {
      var label = (th.dataset.label || th.textContent).replace(/\s*[▲▼]$/, '').trim();
      if (SCORE_COLS.indexOf(label) === -1) return;

      var cells = Array.from(table.querySelectorAll('tbody tr')).map(function (tr) {
        return tr.cells[idx] || null;
      }).filter(Boolean);

      var values = cells.map(function (td) {
        return parseFloat(td.textContent.replace(/[^\d.\-]/g, ''));
      }).filter(function (v) { return !isNaN(v); });

      if (values.length === 0) return;

      var sorted = values.slice().sort(function (a, b) { return a - b; });
      var lo = percentile(sorted, 50);
      var hi = sorted[sorted.length - 1];
      var range = hi - lo;

      cells.forEach(function (td) {
        var v = parseFloat(td.textContent.replace(/[^\d.\-]/g, ''));
        if (isNaN(v)) return;
        var ratio = range > 0 ? (v - lo) / range : 0.5;
        ratio = Math.max(0, Math.min(1, ratio));
        ratio = Math.pow(ratio, 2);
        td.style.backgroundColor = scoreColor(ratio);
      });
    });
  }

  function sortTable(table, colIdx, asc) {
    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort(function (a, b) {
      var va = parseVal(a.cells[colIdx] ? a.cells[colIdx].textContent : '');
      var vb = parseVal(b.cells[colIdx] ? b.cells[colIdx].textContent : '');
      if (va < vb) return asc ? -1 : 1;
      if (va > vb) return asc ? 1 : -1;
      return 0;
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
  }

  document.querySelectorAll('table.results-table').forEach(function (table) {
    var state = { col: -1, asc: true };

    applyScoreColors(table);

    table.querySelectorAll('thead th').forEach(function (th, idx) {
      if (!th.textContent.trim()) return;
      th.dataset.label = th.textContent.trim();
      th.classList.add('sortable');
      th.addEventListener('click', function () {
        var asc = (state.col === idx) ? !state.asc : false;
        state.col = idx;
        state.asc = asc;
        table.querySelectorAll('thead th[data-label]').forEach(function (h) {
          h.textContent = h.dataset.label;
        });
        th.textContent = th.dataset.label + (asc ? ' \u25b2' : ' \u25bc');
        sortTable(table, idx, asc);
      });
    });
  });
})();
