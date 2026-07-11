# US-6.3 — Batch Prediction Endpoint

**Epic**: E6 — Value-Add Features (Cherry on Top)
**Priority**: Could | **Story Points**: 3

## User Story

As an API consumer, I want to submit multiple properties in a single request and receive predictions for all of them at once, so that I can efficiently evaluate an entire portfolio without making hundreds of individual API calls.

## Acceptance Criteria

- [ ] New endpoint `POST /predict/batch` accepts a JSON array of `HomeFeatures` objects
- [ ] Returns a JSON array of predictions in the same order as input
- [ ] Each item in the response includes `predicted_price` (and `confidence_range` if US-6.2 is done)
- [ ] Missing values are handled per-item (same KNN imputation logic)
- [ ] Invalid items return per-item errors without failing the entire batch
- [ ] Maximum batch size is configurable (default: 100) with a clear 400 error if exceeded
- [ ] Batch processing is faster than N sequential `/predict` calls (vectorized where possible)
- [ ] Swagger docs include a multi-item example

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

## Files to Modify/Create

- `src/api/endpoints.py` — new `POST /predict/batch` endpoint
- `src/services/predictor.py` — add `predict_batch()` method
- `test/unit/test_api_unit.py` — tests for batch endpoint (happy path, mixed valid/invalid, max size)
