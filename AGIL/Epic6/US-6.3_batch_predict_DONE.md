# US-6.3 — Batch Prediction Endpoint

**Epic**: E6 — Value-Add Features (Cherry on Top)
**Priority**: Could | **Story Points**: 3
**Status**: DONE

## User Story

As an API consumer, I want to submit multiple properties in a single request and receive predictions for all of them at once, so that I can efficiently evaluate an entire portfolio without making hundreds of individual API calls.

## Acceptance Criteria

- [x] New endpoint `POST /predict/batch` accepts a JSON array of `HomeFeatures` objects
- [x] Returns a JSON array of predictions in the same order as input
- [x] Each item in the response includes `predicted_price` (and `confidence_range` if US-6.2 is done)
- [x] Missing values are handled per-item (same KNN imputation logic)
- [x] Invalid items return per-item errors without failing the entire batch
- [x] Maximum batch size is configurable (default: 100) with a clear 400 error if exceeded
- [x] Batch processing is faster than N sequential `/predict` calls (vectorized where possible)
- [x] Swagger docs include a multi-item example

## Example Request

```json
{
  "properties": [
    {
      "bedrooms": 3,
      "bathrooms": 2.5,
      "sqft_living": 2000,
      "sqft_lot": 5000,
      "floors": 2,
      "sqft_above": 1500,
      "sqft_basement": 500,
      "zipcode": "98125"
    },
    {
      "bedrooms": null,
      "bathrooms": 1.0,
      "sqft_living": 1200,
      "sqft_lot": null,
      "floors": 1,
      "sqft_above": 1200,
      "sqft_basement": 0,
      "zipcode": "98042"
    }
  ]
}
```

## Example Response

```json
{
  "predictions": [
    {
      "index": 0,
      "predicted_price": 450000.0,
      "status": "success"
    },
    {
      "index": 1,
      "predicted_price": 285000.0,
      "status": "success"
    }
  ],
  "total": 2,
  "successful": 2,
  "failed": 0
}
```

## Example Error Response (per-item)

```json
{
  "predictions": [
    {
      "index": 0,
      "predicted_price": 450000.0,
      "status": "success"
    },
    {
      "index": 1,
      "predicted_price": null,
      "status": "error",
      "error": "zipcode not found"
    }
  ],
  "total": 2,
  "successful": 1,
  "failed": 1
}
```

## Technical Notes

- Reuse `HomeFeatures` model for each item in the batch
- Create a `BatchRequest` Pydantic model wrapping a `list[HomeFeatures]`
- Vectorize imputation: pass all rows to `imputer.impute()` at once (KNNImputer supports multi-row)
- Vectorize prediction: pass full DataFrame to `model.predict()` at once
- Per-item error handling: catch `ValueError` per zipcode, don't abort the batch
- Add `MAX_BATCH_SIZE` config (env var or constant) to prevent abuse

## Files Modified/Created

- `src/api/endpoints.py` — new `POST /predict/batch` endpoint + batch models
- `src/services/predictor.py` — added `predict_batch()` method
- `test/unit/test_api_unit.py` — tests for batch endpoint (happy path, mixed valid/invalid, max size, empty, parity with single predict)
- `README.md` — usage docs for single and batch prediction

---

## What Was Done

- Added `POST /predict/batch` that accepts `{ "properties": [ ... ] }` and returns predictions with `total` / `successful` / `failed` summary counts.
- Implemented `PredictionService.predict_batch()` with vectorized KNN imputation, left-merge on demographics, and a single `model.predict()` call for all valid rows.
- Per-item error handling: schema/validation failures and unknown zipcodes return `status: "error"` for that row only; the rest of the batch still succeeds.
- Empty batches (`properties: []`) return an empty result (`total: 0`) with HTTP 200.
- Enforced `MAX_BATCH_SIZE = 100`; oversized batches return HTTP 400 with a clear message.
- Unit tests cover happy path, missing-value imputation, mixed valid/invalid items, empty batch, max size, and parity with single `/predict`.
- README and OpenAPI examples updated for the batch endpoint.

## Attention Points

- `confidence_range` is **not** included because US-6.2 was not implemented; response items only expose `predicted_price` + `status` (+ `error` when failed).
- Batch items are validated one-by-one with `HomeFeatures.model_validate()` so a bad row does not trigger a whole-request 422 (unlike single `/predict`).
- Validation error messages are returned as a single string on the item (field + message), matching the intent of the single-endpoint 422 detail for that row.
- Demographics join uses `merge(..., indicator=True)` so unknown zipcodes are detected reliably without relying on NaN demographic columns.
- `MAX_BATCH_SIZE` is a module constant (100), not an environment variable.

## Business Value

Portfolio and bulk valuation workflows no longer require hundreds of individual API calls. Agents, analysts, and partner systems can submit up to 100 properties in one request, get ordered results back, and keep working even when a few rows are incomplete or invalid — those rows are flagged per item instead of failing the entire job. That reduces integration cost, cuts wait time for large lists, and makes the API practical for day-to-day portfolio screening rather than one-off lookups.

## Example curl (5-property batch)

```bash
curl -X POST http://127.0.0.1:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "properties": [
      {
        "bedrooms": 3,
        "bathrooms": 2.5,
        "sqft_living": 2000,
        "sqft_lot": 5000,
        "floors": 2,
        "sqft_above": 1500,
        "sqft_basement": 500,
        "zipcode": "98125"
      },
      {
        "bedrooms": null,
        "bathrooms": 1.0,
        "sqft_living": 1200,
        "sqft_lot": null,
        "floors": 1,
        "sqft_above": 1200,
        "sqft_basement": 0,
        "zipcode": "98042"
      },
      {
        "bedrooms": 4,
        "bathrooms": 3.0,
        "sqft_living": 2800,
        "sqft_lot": 7000,
        "floors": 2,
        "sqft_above": 2200,
        "sqft_basement": 600,
        "zipcode": "98052"
      },
      {
        "bedrooms": 2,
        "bathrooms": 1.0,
        "sqft_living": 900,
        "sqft_lot": 3000,
        "floors": 1,
        "sqft_above": 900,
        "sqft_basement": 0,
        "zipcode": "98115"
      },
      {
        "bedrooms": 5,
        "bathrooms": 3.5,
        "sqft_living": 3500,
        "sqft_lot": 10000,
        "floors": 2,
        "sqft_above": 2800,
        "sqft_basement": 700,
        "zipcode": "98004"
      }
    ]
  }'
```
