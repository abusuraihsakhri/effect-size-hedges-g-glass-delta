/* Client-side independent-group standardized mean differences. No network requests. */
(function (root) {
  'use strict';

  var fields = ['mean1', 'mean2', 'std1', 'std2', 'n1', 'n2'];
  var outputFields = ['cohens_d', 'hedges_g', 'glasses_delta', 'standard_error', 'classification'];

  function finite(value, label) {
    if (value === null || value === undefined || String(value).trim() === '') {
      throw new Error(label + ' is required.');
    }
    var n = Number(value);
    if (!Number.isFinite(n)) throw new Error(label + ' must be finite.');
    return n;
  }

  function compute(input) {
    var v = {};
    fields.forEach(function (key) { v[key] = finite(input[key], key); });
    if (!Number.isSafeInteger(v.n1) || !Number.isSafeInteger(v.n2) || v.n1 < 2 || v.n2 < 2) {
      throw new Error('Both sample sizes must be integers of at least 2.');
    }
    if (v.std1 < 0 || v.std2 <= 0) {
      throw new Error('Group 1 SD must be non-negative; control (group 2) SD must be positive.');
    }
    var df = v.n1 + v.n2 - 2;
    var pooled = Math.hypot(Math.sqrt(v.n1 - 1) * v.std1, Math.sqrt(v.n2 - 1) * v.std2) / Math.sqrt(df);
    if (!(pooled > 0) || !Number.isFinite(pooled)) throw new Error('Pooled SD must be positive and finite.');
    var d = (v.mean1 - v.mean2) / pooled;
    var g = d * (1 - 3 / (4 * df - 1));
    var delta = (v.mean1 - v.mean2) / v.std2;
    var se = Math.sqrt(1 / v.n1 + 1 / v.n2 + d * d / (2 * (v.n1 + v.n2)));
    if (![d, g, delta, se].every(Number.isFinite)) throw new Error('Calculated effect size is not finite.');
    var a = Math.abs(g);
    return {
      cohens_d: d,
      hedges_g: g,
      glasses_delta: delta,
      standard_error: se,
      classification: a < .2 ? 'Negligible' : a < .5 ? 'Small' : a < .8 ? 'Medium' : 'Large'
    };
  }

  function parseCSV(text) {
    text = String(text).replace(/^\uFEFF/, '');
    var rows = [], row = [], cell = '', quoted = false;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (quoted) {
        if (c === '"') {
          if (text[i + 1] === '"') { cell += '"'; i++; }
          else quoted = false;
        } else { cell += c; }
      } else if (c === '"' && cell === '') {
        quoted = true;
      } else if (c === ',') {
        row.push(cell); cell = '';
      } else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(cell); cell = '';
        if (row.some(function (x) { return x.trim() !== ''; })) rows.push(row);
        row = [];
      } else if (c === '"') {
        throw new Error('Unexpected quote in CSV field.');
      } else { cell += c; }
    }
    if (quoted) throw new Error('Unclosed quoted CSV field.');
    row.push(cell);
    if (row.some(function (x) { return x.trim() !== ''; })) rows.push(row);
    return rows;
  }

  function escapeCSV(value) {
    var s = String(value === undefined || value === null ? '' : value);
    // Neutralize spreadsheet formulas in user-supplied text on CSV export.
    if (/^\s*[=+@-]/.test(s) && !/^[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?$/.test(s.trim())) s = "'" + s;
    return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function toCSV(rows) {
    return rows.map(function (row) { return row.map(escapeCSV).join(','); }).join('\r\n') + '\r\n';
  }

  function batch(text) {
    var rows = parseCSV(text);
    if (rows.length === 0) throw new Error('CSV is empty.');
    if (rows.length > 10001) throw new Error('Maximum 10,000 data rows per file.');
    var headers = rows.shift().map(function (x) { return x.trim(); });
    if (new Set(headers).size !== headers.length || headers.some(function (h) { return !h; })) {
      throw new Error('CSV column headers must be unique and non-empty.');
    }
    fields.forEach(function (field) {
      if (!headers.includes(field)) throw new Error('Missing CSV column: ' + field);
    });
    var resultHeaders = headers.concat(outputFields.filter(function (x) { return !headers.includes(x); }));
    var values = rows.map(function (row, index) {
      if (row.length !== headers.length) throw new Error('CSV row ' + (index + 2) + ' has incorrect column count.');
      var input = {};
      headers.forEach(function (h, j) { input[h] = row[j]; });
      var metrics;
      try { metrics = compute(input); }
      catch (err) { throw new Error('CSV row ' + (index + 2) + ': ' + err.message); }
      return resultHeaders.map(function (h) {
        return Object.prototype.hasOwnProperty.call(metrics, h)
          ? (typeof metrics[h] === 'number' ? metrics[h].toFixed(4) : metrics[h])
          : input[h];
      });
    });
    return { csv: toCSV([resultHeaders].concat(values)), count: values.length };
  }

  var api = { compute: compute, parseCSV: parseCSV, batch: batch, toCSV: toCSV };
  root.EffectSizes = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;

  if (typeof document === 'undefined') return;
  var form = document.getElementById('effect-form');
  if (!form) return;
  var status = document.getElementById('status');
  var results = document.getElementById('results');
  var csvFile = document.getElementById('csv-file');
  var download = document.getElementById('download');
  var exportContent = '';

  function message(text, error) {
    status.textContent = text;
    status.setAttribute('role', error ? 'alert' : 'status');
    status.className = error ? 'error' : 'notice';
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    try {
      var input = {};
      fields.forEach(function (key) { input[key] = document.getElementById(key).value; });
      var r = compute(input);
      outputFields.forEach(function (key) {
        document.getElementById('result-' + key).textContent =
          typeof r[key] === 'number' ? r[key].toFixed(4) : r[key];
      });
      results.hidden = false;
      message('Calculated locally. Positive values mean group 1 is higher than group 2.', false);
    } catch (err) {
      results.hidden = true;
      message(err.message, true);
    }
  });

  csvFile.addEventListener('change', async function () {
    exportContent = '';
    download.disabled = true;
    var file = csvFile.files && csvFile.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      message('CSV must be 2 MB or smaller.', true);
      return;
    }
    try {
      var result = batch(await file.text());
      exportContent = result.csv;
      download.disabled = false;
      message(result.count + ' CSV rows validated and calculated locally. Ready to export.', false);
    } catch (err) {
      message(err.message, true);
    }
  });

  download.addEventListener('click', function () {
    if (!exportContent) return;
    var url = URL.createObjectURL(new Blob([exportContent], { type: 'text/csv;charset=utf-8' }));
    var a = document.createElement('a');
    a.href = url;
    a.download = 'effect-size-results.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });
})(typeof window === 'undefined' ? globalThis : window);
