(function () {
  function parseVal(text) {
    var s = text.trim();
    var n = parseFloat(s.replace(/[^\d.\-]/g, ''));
    return isNaN(n) ? s.toLowerCase() : n;
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
    table.querySelectorAll('thead th').forEach(function (th, idx) {
      if (!th.textContent.trim()) return; // skip blank deduction-cell headers
      th.dataset.label = th.textContent.trim();
      th.classList.add('sortable');
      th.addEventListener('click', function () {
        var asc = (state.col === idx) ? !state.asc : false;
        state.col = idx;
        state.asc = asc;
        // Reset all headers, then set indicator on active one
        table.querySelectorAll('thead th[data-label]').forEach(function (h) {
          h.textContent = h.dataset.label;
        });
        th.textContent = th.dataset.label + (asc ? ' \u25b2' : ' \u25bc');
        sortTable(table, idx, asc);
      });
    });
  });
})();
