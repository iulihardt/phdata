(function () {
  "use strict";

  // ── DOM refs ────────────────────────────────────────────
  const infoLat = document.getElementById("info-lat");
  const infoLon = document.getElementById("info-lon");
  const infoZip = document.getElementById("info-zip");
  const infoCity = document.getElementById("info-city");
  const infoState = document.getElementById("info-state");
  const geoStatus = document.getElementById("geo-status");

  const predictionValue = document.getElementById("prediction-value");
  const predictionStatus = document.getElementById("prediction-status");
  const predictionCard = document.querySelector(".prediction-card");

  const sliderIds = ["bedrooms", "bathrooms", "sqft_living", "sqft_lot", "floors"];
  const integerSliders = new Set(["bedrooms", "bathrooms", "floors"]);

  // ── State ───────────────────────────────────────────────
  let currentZipcode = null;
  let marker = null;

  // ── Map init ────────────────────────────────────────────
  const map = L.map("map").setView([47.6062, -122.3321], 10);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map);

  // ── Helpers ─────────────────────────────────────────────
  function formatUSD(value) {
    return "$" + Math.round(value).toLocaleString("en-US");
  }

  function formatNumber(value) {
    return Number(value).toLocaleString("en-US");
  }

  function showStatus(el, msg, type) {
    el.textContent = msg;
    el.className = "status-msg " + type;
  }

  function hideStatus(el) {
    el.className = "status-msg hidden";
  }

  function debounce(fn, ms) {
    let timer;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(fn, ms);
    };
  }

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
        const body = await resp.json().catch(function () {
          return {};
        });
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
    predictionCard.classList.remove("active");
    hideStatus(predictionStatus);
  }

  async function runPrediction() {
    if (!currentZipcode) return;

    showStatus(predictionStatus, "Calculating...", "loading");

    var payload = { zipcode: currentZipcode };
    sliderIds.forEach(function (id) {
      var raw = document.getElementById(id).value;
      payload[id] = integerSliders.has(id) ? parseInt(raw, 10) : parseFloat(raw);
    });

    try {
      var resp = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        var body = await resp.json().catch(function () {
          return {};
        });
        var detail = body.detail || "Prediction failed";
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
        predictionCard.classList.remove("active");
        return;
      }

      var data = await resp.json();
      predictionValue.textContent = formatUSD(data.predicted_price);
      predictionCard.classList.add("active");
      hideStatus(predictionStatus);
    } catch (err) {
      showStatus(predictionStatus, "Network error", "error");
      predictionValue.textContent = "—";
      predictionCard.classList.remove("active");
    }
  }

  var debouncedPredict = debounce(runPrediction, 300);

  // ── Map click / marker ─────────────────────────────────
  function onLocationSelected(lat, lon) {
    reverseGeocode(lat, lon);
  }

  map.on("click", function (e) {
    var lat = e.latlng.lat;
    var lon = e.latlng.lng;

    if (marker) {
      marker.setLatLng(e.latlng);
    } else {
      marker = L.marker(e.latlng, { draggable: true }).addTo(map);

      marker.on("dragend", function (ev) {
        var pos = ev.target.getLatLng();
        onLocationSelected(pos.lat, pos.lng);
      });
    }

    onLocationSelected(lat, lon);
  });

  // ── Slider wiring ──────────────────────────────────────
  sliderIds.forEach(function (id) {
    var slider = document.getElementById(id);
    var display = document.getElementById(id + "-val");

    function update() {
      var val = integerSliders.has(id)
        ? parseInt(slider.value, 10)
        : parseFloat(slider.value);
      if (id === "sqft_living" || id === "sqft_lot") {
        display.textContent = formatNumber(val);
      } else {
        display.textContent = val;
      }
      debouncedPredict();
    }

    slider.addEventListener("input", update);
  });
})();
