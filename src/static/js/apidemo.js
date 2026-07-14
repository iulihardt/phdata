(function () {
  "use strict";

  // ── Preset payloads ────────────────────────────────────
  var SINGLE_FULL = {
    bedrooms: 3,
    bathrooms: 2.5,
    sqft_living: 2000,
    sqft_lot: 5000,
    floors: 2,
    sqft_above: 1500,
    sqft_basement: 500,
    zipcode: "98125",
  };

  var SINGLE_MISSING = {
    bedrooms: 3,
    bathrooms: null,
    sqft_living: 2000,
    sqft_lot: null,
    floors: 2,
    sqft_above: 1500,
    sqft_basement: 500,
    zipcode: "98125",
  };

  var BATCH_DEFAULT = {
    properties: [
      { bedrooms: 3, bathrooms: 2.5, sqft_living: 2000, sqft_lot: 5000, floors: 2, sqft_above: 1500, sqft_basement: 500, zipcode: "98125" },
      { bedrooms: null, bathrooms: 1.0, sqft_living: 1200, sqft_lot: null, floors: 1, sqft_above: 1200, sqft_basement: 0, zipcode: "98042" },
      { bedrooms: 2, bathrooms: 1, sqft_living: 900, sqft_lot: 1000, floors: 1, sqft_above: 900, sqft_basement: 0, zipcode: "00000" },
    ],
  };

  // ── DOM refs ────────────────────────────────────────────
  var singleBody = document.getElementById("single-body");
  var batchBody = document.getElementById("batch-body");

  // Prefill textareas
  singleBody.value = JSON.stringify(SINGLE_FULL, null, 2);
  batchBody.value = JSON.stringify(BATCH_DEFAULT, null, 2);

  // ── Helpers ─────────────────────────────────────────────
  function pretty(obj) {
    return JSON.stringify(obj, null, 2);
  }

  function formatUSD(v) {
    return "$" + Math.round(v).toLocaleString("en-US");
  }

  function ms(v) {
    return v.toFixed(1) + " ms";
  }

  // ── JSON syntax highlight ──────────────────────────────
  function highlightJSON(jsonStr) {
    return jsonStr
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(
        /("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
          var cls = "json-number";
          if (/^"/.test(match)) {
            cls = /:$/.test(match) ? "json-key" : "json-string";
          } else if (/true|false/.test(match)) {
            cls = "json-boolean";
          } else if (/null/.test(match)) {
            cls = "json-null";
          }
          return '<span class="' + cls + '">' + match + "</span>";
        }
      );
  }

  // ── Resource Timing helper ─────────────────────────────
  function getResourceTiming(urlFragment) {
    var entries = performance.getEntriesByType("resource");
    for (var i = entries.length - 1; i >= 0; i--) {
      if (entries[i].name.indexOf(urlFragment) !== -1) {
        return entries[i];
      }
    }
    return null;
  }

  // ── Timing bar renderer ────────────────────────────────
  function renderTimingBar(barEl, legendEl, totalEl, timing) {
    var total = timing.total;
    if (total <= 0) total = 1;

    var backendPct = Math.max((timing.backend / total) * 100, 2);
    var transferPct = Math.max((timing.transfer / total) * 100, 1);
    var frontendPct = Math.max(100 - backendPct - transferPct, 2);

    barEl.innerHTML =
      '<div class="h-full bg-brand" style="width:' + backendPct + '%" title="Backend"></div>' +
      '<div class="h-full bg-amber-400" style="width:' + transferPct + '%" title="Transfer"></div>' +
      '<div class="h-full bg-emerald-400" style="width:' + frontendPct + '%" title="Frontend"></div>';

    legendEl.innerHTML =
      '<span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-brand"></span>Backend: ' + ms(timing.backend) + "</span>" +
      '<span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-amber-400"></span>Transfer: ' + ms(timing.transfer) + "</span>" +
      '<span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400"></span>Frontend: ' + ms(timing.frontend) + "</span>";

    totalEl.textContent = "Total: " + ms(timing.total);
  }

  // ── Status badge helper ────────────────────────────────
  function renderStatusBadge(el, statusCode) {
    el.textContent = statusCode + " " + (statusCode === 200 ? "OK" : statusCode < 500 ? "Client Error" : "Server Error");
    if (statusCode === 200) {
      el.className = "badge badge-success text-xs font-semibold";
    } else if (statusCode < 500) {
      el.className = "badge badge-warning text-xs font-semibold";
    } else {
      el.className = "badge badge-error text-xs font-semibold";
    }
  }

  // ── Tab switching ──────────────────────────────────────
  document.querySelectorAll(".tab[data-panel]").forEach(function (tab) {
    tab.addEventListener("click", function () {
      var panel = tab.dataset.panel;
      var target = tab.dataset.tab;

      tab.parentElement.querySelectorAll(".tab").forEach(function (t) {
        t.classList.remove("tab-active");
      });
      tab.classList.add("tab-active");

      var responseEl = document.getElementById(panel + "-response-json");
      var requestEl = document.getElementById(panel + "-request-json");

      if (target === "response") {
        responseEl.classList.remove("hidden");
        requestEl.classList.add("hidden");
      } else {
        responseEl.classList.add("hidden");
        requestEl.classList.remove("hidden");
      }
    });
  });

  // ── Generic API caller with timing ─────────────────────
  async function callAPI(url, bodyStr) {
    var parsed;
    try {
      parsed = JSON.parse(bodyStr);
    } catch (e) {
      throw new Error("Invalid JSON in request body: " + e.message);
    }

    performance.clearResourceTimings();
    var t0 = performance.now();

    var resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsed),
    });

    var tHeaders = performance.now();
    var data = await resp.json();
    var tDone = performance.now();

    var timing = { backend: 0, transfer: 0, frontend: tDone - tHeaders, total: tDone - t0 };

    // Try Resource Timing API for more accurate backend measurement
    await new Promise(function (r) { setTimeout(r, 10); });
    var entry = getResourceTiming(url);
    if (entry && entry.responseStart > 0 && entry.requestStart > 0) {
      timing.backend = entry.responseStart - entry.requestStart;
      timing.transfer = entry.responseEnd - entry.responseStart;
    } else {
      timing.backend = tHeaders - t0;
      timing.transfer = 0;
    }

    return { status: resp.status, data: data, sent: parsed, timing: timing };
  }

  // ── Single predict ─────────────────────────────────────
  document.getElementById("btn-single").addEventListener("click", async function () {
    var btn = this;
    btn.classList.add("loading");
    btn.disabled = true;

    var resultEl = document.getElementById("single-result");

    try {
      var res = await callAPI("/predict", singleBody.value);

      renderStatusBadge(document.getElementById("single-status"), res.status);
      renderTimingBar(
        document.getElementById("single-bar"),
        document.getElementById("single-timing-legend"),
        document.getElementById("single-total"),
        res.timing
      );

      document.getElementById("single-request-json").innerHTML = highlightJSON(pretty({
        method: "POST",
        url: "/predict",
        body: res.sent,
      }));
      document.getElementById("single-response-json").innerHTML = highlightJSON(pretty(res.data));

      resultEl.classList.remove("hidden");
    } catch (err) {
      renderStatusBadge(document.getElementById("single-status"), 0);
      document.getElementById("single-status").textContent = "Error";
      document.getElementById("single-status").className = "badge badge-error text-xs font-semibold";
      document.getElementById("single-response-json").innerHTML = highlightJSON(pretty({ error: err.message }));
      document.getElementById("single-request-json").innerHTML = "";
      document.getElementById("single-bar").innerHTML = "";
      document.getElementById("single-timing-legend").innerHTML = "";
      document.getElementById("single-total").textContent = "";
      resultEl.classList.remove("hidden");
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  });

  // ── Batch predict ──────────────────────────────────────
  document.getElementById("btn-batch").addEventListener("click", async function () {
    var btn = this;
    btn.classList.add("loading");
    btn.disabled = true;

    var resultEl = document.getElementById("batch-result");

    try {
      var res = await callAPI("/predict/batch", batchBody.value);

      renderStatusBadge(document.getElementById("batch-status"), res.status);
      renderTimingBar(
        document.getElementById("batch-bar"),
        document.getElementById("batch-timing-legend"),
        document.getElementById("batch-total-time"),
        res.timing
      );

      // Summary stats
      var d = res.data;
      var statsEl = document.getElementById("batch-stats");
      statsEl.innerHTML =
        '<div class="stat-card bg-gray-50 rounded-xl px-4 py-2 text-center flex-1">' +
          '<div class="text-2xl font-bold text-gray-800">' + (d.total || 0) + '</div>' +
          '<div class="text-xs text-gray-500">Total</div>' +
        '</div>' +
        '<div class="stat-card bg-emerald-50 rounded-xl px-4 py-2 text-center flex-1">' +
          '<div class="text-2xl font-bold text-emerald-600">' + (d.successful || 0) + '</div>' +
          '<div class="text-xs text-gray-500">Successful</div>' +
        '</div>' +
        '<div class="stat-card bg-red-50 rounded-xl px-4 py-2 text-center flex-1">' +
          '<div class="text-2xl font-bold text-red-500">' + (d.failed || 0) + '</div>' +
          '<div class="text-xs text-gray-500">Failed</div>' +
        '</div>';

      // Table
      var tbody = document.getElementById("batch-table-body");
      tbody.innerHTML = "";
      if (d.predictions) {
        d.predictions.forEach(function (p) {
          var statusBadge = p.status === "success"
            ? '<span class="badge badge-success badge-xs">success</span>'
            : '<span class="badge badge-error badge-xs">error</span>';
          var price = p.predicted_price != null ? formatUSD(p.predicted_price) : "—";
          var error = p.error || "—";

          tbody.innerHTML +=
            "<tr>" +
            "<td class='font-mono'>" + p.index + "</td>" +
            "<td>" + statusBadge + "</td>" +
            "<td class='font-semibold'>" + price + "</td>" +
            "<td class='text-xs text-gray-500 max-w-[200px] truncate' title='" + error.replace(/'/g, "&#39;") + "'>" + error + "</td>" +
            "</tr>";
        });
      }

      document.getElementById("batch-request-json").innerHTML = highlightJSON(pretty({
        method: "POST",
        url: "/predict/batch",
        body: res.sent,
      }));
      document.getElementById("batch-response-json").innerHTML = highlightJSON(pretty(res.data));

      resultEl.classList.remove("hidden");
    } catch (err) {
      renderStatusBadge(document.getElementById("batch-status"), 0);
      document.getElementById("batch-status").textContent = "Error";
      document.getElementById("batch-status").className = "badge badge-error text-xs font-semibold";
      document.getElementById("batch-response-json").innerHTML = highlightJSON(pretty({ error: err.message }));
      document.getElementById("batch-request-json").innerHTML = "";
      document.getElementById("batch-bar").innerHTML = "";
      document.getElementById("batch-timing-legend").innerHTML = "";
      document.getElementById("batch-total-time").textContent = "";
      document.getElementById("batch-stats").innerHTML = "";
      document.getElementById("batch-table-body").innerHTML = "";
      resultEl.classList.remove("hidden");
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  });

  // ── Presets ─────────────────────────────────────────────
  document.getElementById("preset-full").addEventListener("click", function () {
    singleBody.value = pretty(SINGLE_FULL);
  });
  document.getElementById("preset-missing").addEventListener("click", function () {
    singleBody.value = pretty(SINGLE_MISSING);
  });
})();
