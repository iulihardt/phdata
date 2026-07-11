Here is the user story in Markdown format.

# User Story: Interactive House Price Prediction Map

**Story ID:** US-005

## Title

Interactive Map for House Price Prediction

---

## User Story

**As a** user,

**I want** to select a property's location by clicking on an interactive map,

**So that** the ZIP Code is automatically determined and I can instantly estimate the house price without manually entering geographic information.

---

# Description

Create a new page available at:

```text
/directmap
```

The page should provide an interactive interface where the map is the primary way to select the property's location.

The map must be centered on the continental United States using **Leaflet** with **OpenStreetMap** tiles.

When the user clicks anywhere on the map:

* A marker should be placed at the selected location.
* Latitude and longitude should be captured.
* A reverse geocoding service should retrieve the corresponding ZIP Code.
* The ZIP Code should automatically populate the prediction model.
* The house price prediction should update immediately.

The remaining house attributes should be configurable using sliders.

The predicted price should refresh automatically whenever any input changes.

---

# Functional Requirements

## Interactive Map

* Create a new route at `/directmap`.
* Display an interactive Leaflet map.
* Use OpenStreetMap tiles.
* Center the map on the continental United States.
* Allow users to click anywhere on the map.
* Display a draggable marker.
* Moving the marker updates the selected location.

---

## Reverse Geocoding

When the marker is placed or moved:

* Capture latitude and longitude.
* Retrieve the corresponding ZIP Code using a reverse geocoding service (e.g., Nominatim/OpenStreetMap).
* Automatically update the ZIP Code used by the prediction model.

---

## Prediction

The prediction should execute automatically whenever one of the following values changes:

* Bedrooms
* Bathrooms
* Living Area (sqft)
* Lot Size (sqft)
* Floors
* Property location (ZIP Code)

No **Predict** button is required.

---

## Property Inputs

Display interactive sliders for:

* Bedrooms
* Bathrooms
* Living Area (sqft)
* Lot Size (sqft)
* Floors

Each slider should display its current value.

---

## Prediction Result

Display the estimated property value in a prominent prediction card.

Example:

```text
Estimated House Price

$824,350
```

The prediction should update in real time without requiring a page reload.

---

## Location Information

Display the selected location details:

* Latitude
* Longitude
* ZIP Code
* City
* State

---

# Acceptance Criteria

* [x] A new `/directmap` page is available.
* [x] The Leaflet map loads successfully.
* [x] The map is centered on the United States.
* [x] Clicking on the map places a marker.
* [x] The marker can be dragged to another location.
* [x] Latitude and longitude are updated after every movement.
* [x] Reverse geocoding retrieves the correct ZIP Code.
* [x] The ZIP Code is automatically used by the prediction model.
* [x] Property attribute sliders update the prediction automatically.
* [x] The estimated house price refreshes without reloading the page.
* [x] Loading and error states are handled gracefully.

---

# Technical Notes

## Frontend

* HTML + Jinja2
* Leaflet.js
* OpenStreetMap
* JavaScript Fetch API
* Debounce prediction requests (approximately 300 ms)

## Backend

* FastAPI
* Existing `/predict` endpoint
* Reverse geocoding integration
* Existing `HomeFeatures` Pydantic model

---

# Non-Functional Requirements

* Responsive layout for desktop and tablet.
* Prediction updates should complete in under one second under normal conditions.
* Map interactions should remain smooth while predictions are being calculated.

---

# Out of Scope

* Address search or autocomplete
* Satellite imagery
* Property boundary visualization
* Saving prediction history
* User authentication

---

# Future Enhancements

* Address search with autocomplete.
* Heatmap of predicted home values.
* Confidence interval for predictions.
* Comparable nearby properties.
* Historical prediction tracking.
* Satellite map layer.
* Support for multiple prediction models.

---

# Implementation Summary

## What Was Done

A fully functional interactive map page was implemented at `/directmap`, enabling users to estimate property values by clicking a location on a map rather than manually entering geographic data. The implementation includes:

* **Interactive Leaflet map** centered on the Seattle area (where the ML model has coverage), using OpenStreetMap tiles. Users can click anywhere to place a draggable marker.
* **Server-side reverse geocoding** via a new `GET /reverse-geocode` FastAPI endpoint that proxies requests to the Nominatim/OpenStreetMap service. This approach respects Nominatim's usage policy by sending a proper `User-Agent` header and avoids browser-side CORS and rate-limit issues.
* **Real-time price prediction** triggered automatically whenever the location or any property slider changes. Predictions are debounced at 300 ms to prevent excessive API calls during rapid interactions.
* **Property feature sliders** for Bedrooms, Bathrooms, Living Area (sqft), Lot Size (sqft), and Floors, each displaying its current value.
* **Location information panel** showing the resolved Latitude, Longitude, ZIP Code, City, and State.
* **Prominent prediction card** displaying the estimated house price formatted as USD, with visual feedback when a prediction is active.
* **Graceful error handling** for unsupported ZIP codes (outside the Seattle/King County area), geocoding timeouts, network failures, and locations without a resolvable ZIP code (e.g., ocean clicks).
* **Responsive layout** that works on both desktop and tablet screens.
* **Unit tests** covering the `/directmap` page rendering, successful reverse geocoding, missing ZIP code handling, timeout handling, and missing parameter validation — all using mocked external dependencies.

### Files Added or Modified

| File | Change |
|------|--------|
| `requirements.txt` | Added `jinja2` and `httpx` dependencies |
| `src/main.py` | Wired up Jinja2Templates, StaticFiles mount, and the new web router |
| `src/api/web.py` | New router with `GET /directmap` and `GET /reverse-geocode` endpoints |
| `src/templates/directmap.html` | Jinja2 template for the interactive map page |
| `src/static/css/directmap.css` | Styling for the map layout, cards, sliders, and status messages |
| `src/static/js/directmap.js` | Client-side logic: Leaflet map, marker, geocoding, debounced prediction, slider wiring |
| `test/unit/test_api_unit.py` | 6 new unit tests for the map page and reverse-geocode endpoint |

## Points of Attention

1. **Seattle-area ZIP code coverage only.** The ML model and demographic dataset cover King County (Seattle area) ZIP codes exclusively. When a user clicks outside this region, the prediction endpoint returns a 400 error, and the UI displays a clear "ZIP code not supported" message. The map defaults to the Seattle area to guide users toward valid locations.

2. **Nominatim usage policy and rate limits.** The reverse geocoding service (Nominatim) is free but subject to a maximum of 1 request per second and requires a valid `User-Agent` header. The server-side proxy enforces this. For a production deployment with high traffic, a dedicated Nominatim instance or a commercial geocoding provider should be considered.

3. **Outbound internet dependency.** The container requires outbound internet access to reach the Nominatim API. This is standard for local development but should be accounted for in network-restricted production environments.

4. **Debounce strategy.** Prediction requests are debounced at 300 ms. This prevents flooding the API during rapid slider adjustments or repeated map clicks, while keeping the experience feeling responsive.

5. **No "Predict" button.** By design, predictions fire automatically. Users do not need to click a button after adjusting inputs. The system relies on debouncing to batch rapid changes.

## Expected Business Improvement

This feature transforms the property valuation experience from a data-entry exercise into an intuitive, visual interaction. Instead of requiring users to know and type a ZIP code, they simply click a location on a familiar map interface.

**Key benefits for Sound Realty:**

* **Lower friction for first-time users.** Real estate professionals and homeowners can explore property values across neighborhoods without needing to look up ZIP codes, reducing the barrier to obtaining estimates.
* **Faster exploration of multiple locations.** Users can quickly compare estimated values across different neighborhoods by clicking or dragging the marker, enabling more efficient market analysis.
* **Improved engagement and trust.** The visual map interface with real-time price updates creates a more polished, professional impression of the tool, reinforcing confidence in the estimates it provides.
* **Foundation for richer geospatial features.** This map-based architecture opens the door for future enhancements such as heat maps of predicted values, comparable property overlays, and neighborhood-level analytics.
