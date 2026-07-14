(function () {
  "use strict";

  // ── Feature configuration ──────────────────────────────
  // label, range bounds, default value, step, and whether it's an integer.
  const FEATURES = [
    { id: "bedrooms",      label: "Bedrooms",                 min: 0,   max: 10,     value: 3,    step: 1,   integer: true },
    { id: "bathrooms",     label: "Bathrooms",                min: 0,   max: 8,      value: 2,    step: 0.5, integer: false },
    { id: "sqft_living",   label: "Living Area (sqft)",       min: 200, max: 10000,  value: 1500, step: 50,  integer: false },
    { id: "sqft_lot",      label: "Lot Size (sqft)",          min: 500, max: 100000, value: 5000, step: 100, integer: false },
    { id: "floors",        label: "Floors",                   min: 1,   max: 4,      value: 1,    step: 1,   integer: true },
    { id: "sqft_above",    label: "Above-Ground Area (sqft)", min: 0,   max: 10000,  value: 1200, step: 50,  integer: false },
    { id: "sqft_basement", label: "Basement Area (sqft)",     min: 0,   max: 5000,   value: 0,    step: 50,  integer: false },
  ];

  const featureById = {};
  FEATURES.forEach(function (f) { featureById[f.id] = f; });

  const nullState = {};
  FEATURES.forEach(function (f) { nullState[f.id] = false; });

  // ── DOM refs ────────────────────────────────────────────
  const infoLat = document.getElementById("info-lat");
  const infoLon = document.getElementById("info-lon");
  const infoZip = document.getElementById("info-zip");
  const infoCity = document.getElementById("info-city");
  const infoState = document.getElementById("info-state");
  const geoStatus = document.getElementById("geo-status");

  const predictionValue = document.getElementById("prediction-value");
  const predictionStatus = document.getElementById("prediction-status");
  const predictionCard = document.getElementById("prediction-card");

  const featuresContainer = document.getElementById("features");
  const featureTemplate = document.getElementById("feature-template");

  // ── State ───────────────────────────────────────────────
  let currentZipcode = null;
  let marker = null;

  // ── Helpers ─────────────────────────────────────────────
  function formatUSD(value) {
    return "$" + Math.round(value).toLocaleString("en-US");
  }

  function formatNumber(value) {
    return Number(value).toLocaleString("en-US");
  }

  function formatSliderValue(id, rawValue) {
    const f = featureById[id];
    const val = f.integer ? parseInt(rawValue, 10) : parseFloat(rawValue);
    return formatNumber(val);
  }

  const STATUS_CLASSES = {
    loading: "bg-gray-100 text-gray-600",
    warning: "bg-amber-50 text-amber-700",
    error: "bg-red-50 text-red-600",
  };

  function showStatus(el, msg, type) {
    el.textContent = msg;
    el.className =
      "mt-1 text-xs rounded-lg px-2 py-1.5 w-full " +
      (STATUS_CLASSES[type] || STATUS_CLASSES.loading);
  }

  function hideStatus(el) {
    el.classList.add("hidden");
  }

  function debounce(fn, ms) {
    let timer;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(fn, ms);
    };
  }

  // ── Build feature rows from config ─────────────────────
  FEATURES.forEach(function (f) {
    const node = featureTemplate.content.firstElementChild.cloneNode(true);
    node.id = "sg-" + f.id;

    const label = node.querySelector(".feature-label");
    label.setAttribute("for", f.id);
    label.textContent = f.label;

    const display = node.querySelector(".val-display");
    display.id = f.id + "-val";
    display.textContent = formatNumber(f.value);

    const slider = node.querySelector(".feature-slider");
    slider.id = f.id;
    slider.min = f.min;
    slider.max = f.max;
    slider.step = f.step;
    slider.value = f.value;

    const toggle = node.querySelector(".null-toggle");
    toggle.dataset.target = f.id;

    featuresContainer.appendChild(node);
  });

  // ── Map init ────────────────────────────────────────────
  const map = L.map("map").setView([47.6062, -122.3321], 10);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map);

  // ── Reverse geocoding ──────────────────────────────────
  async function reverseGeocode(lat, lon) {
    infoLat.textContent = lat.toFixed(5);
    infoLon.textContent = lon.toFixed(5);
    infoZip.textContent = "...";
    infoCity.textContent = "...";
    infoState.textContent = "...";
    showStatus(geoStatus, "Resolving location...", "loading");

    try {
      const resp = await fetch(
        "/reverse-geocode?lat=" +
          encodeURIComponent(lat) +
          "&lon=" +
          encodeURIComponent(lon)
      );

      if (!resp.ok) {
        const body = await resp.json().catch(function () { return {}; });
        const detail = body.detail || "Could not resolve location";
        showStatus(geoStatus, detail, "warning");
        currentZipcode = null;
        infoZip.textContent = "—";
        infoCity.textContent = "—";
        infoState.textContent = "—";
        clearPrediction();
        return;
      }

      const data = await resp.json();
      currentZipcode = data.zipcode;
      infoZip.textContent = data.zipcode;
      infoCity.textContent = data.city || "—";
      infoState.textContent = data.state || "—";
      hideStatus(geoStatus);
      debouncedPredict();
    } catch (err) {
      showStatus(geoStatus, "Geocoding failed: network error", "error");
      currentZipcode = null;
      clearPrediction();
    }
  }

  // ── Prediction ─────────────────────────────────────────
  function clearPrediction() {
    predictionValue.textContent = "—";
    predictionCard.classList.remove("ring-brand");
    predictionCard.classList.add("ring-gray-200");
    hideStatus(predictionStatus);
  }

  async function runPrediction() {
    if (!currentZipcode) return;

    showStatus(predictionStatus, "Calculating...", "loading");

    const payload = { zipcode: currentZipcode };
    FEATURES.forEach(function (f) {
      if (nullState[f.id]) {
        payload[f.id] = null;
        return;
      }
      const raw = document.getElementById(f.id).value;
      payload[f.id] = f.integer ? parseInt(raw, 10) : parseFloat(raw);
    });

    try {
      const resp = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const body = await resp.json().catch(function () { return {}; });
        const detail = body.detail || "Prediction failed";
        if (typeof detail === "string" && detail.includes("zipcode")) {
          showStatus(
            predictionStatus,
            "This ZIP code is not supported by the model (Seattle area only).",
            "warning"
          );
        } else {
          showStatus(predictionStatus, String(detail), "error");
        }
        predictionValue.textContent = "—";
        predictionCard.classList.remove("ring-brand");
        predictionCard.classList.add("ring-gray-200");
        return;
      }

      const data = await resp.json();
      predictionValue.textContent = formatUSD(data.predicted_price);
      predictionCard.classList.add("ring-brand");
      predictionCard.classList.remove("ring-gray-200");
      hideStatus(predictionStatus);
    } catch (err) {
      showStatus(predictionStatus, "Network error", "error");
      predictionValue.textContent = "—";
      predictionCard.classList.remove("ring-brand");
      predictionCard.classList.add("ring-gray-200");
    }
  }

  const debouncedPredict = debounce(runPrediction, 300);

  // ── Map click / marker ─────────────────────────────────
  function onLocationSelected(lat, lon) {
    reverseGeocode(lat, lon);
  }

  map.on("click", function (e) {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;

    if (marker) {
      marker.setLatLng(e.latlng);
    } else {
      marker = L.marker(e.latlng, { draggable: true }).addTo(map);
      marker.on("dragend", function (ev) {
        const pos = ev.target.getLatLng();
        onLocationSelected(pos.lat, pos.lng);
      });
    }

    onLocationSelected(lat, lon);
  });

  // ── Slider wiring (auto-predict, no reload) ────────────
  FEATURES.forEach(function (f) {
    const slider = document.getElementById(f.id);
    const display = document.getElementById(f.id + "-val");

    slider.addEventListener("input", function () {
      if (nullState[f.id]) return;
      display.textContent = formatSliderValue(f.id, slider.value);
      debouncedPredict();
    });
  });

  // ── "I don't know this value" toggle ──────────────────
  document.querySelectorAll(".null-toggle").forEach(function (cb) {
    cb.addEventListener("change", function () {
      const id = cb.dataset.target;
      nullState[id] = cb.checked;

      const group = document.getElementById("sg-" + id);
      const display = document.getElementById(id + "-val");
      const slider = document.getElementById(id);
      const nullLabel = group.querySelector(".null-label");

      if (cb.checked) {
        group.classList.add("is-null");
        display.textContent = "auto-estimated";
        nullLabel.textContent = "I'll set this value";
      } else {
        group.classList.remove("is-null");
        display.textContent = formatSliderValue(id, slider.value);
        nullLabel.textContent = "I don't know this value";
      }

      debouncedPredict();
    });
  });
})();
