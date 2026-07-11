# US-6.2 — Confidence Interval in Predictions

**Epic**: E6 — Value-Add Features (Cherry on Top)
**Priority**: Could | **Story Points**: 3

## User Story

As an API consumer, I want the prediction response to include a confidence range alongside the point estimate, so that I can assess how certain the model is and make better-informed decisions.

## Acceptance Criteria

- [ ] The `/predict` response includes a `confidence_range` field: `[lower_bound, upper_bound]`
- [ ] The interval is based on the variance of similar properties in the training data
- [ ] When all fields are provided (no imputation), the interval is narrower
- [ ] When fields are imputed, the interval is wider (reflecting higher uncertainty)
- [ ] The point estimate (`predicted_price`) remains unchanged (backward-compatible)
- [ ] Swagger docs describe the new field with an example

## Example Response

```json
{
  "predicted_price": 450000.0,
  "confidence_range": [415000.0, 485000.0]
}
```

## Technical Approach

**Option A — KNN Neighbor Variance (recommended for simplicity):**
- After KNN imputation, the K nearest neighbors are already identified
- Retrieve the actual sale prices of those K neighbors from the training set
- Compute the standard deviation of those prices
- Confidence range = `[prediction - 1.5*std, prediction + 1.5*std]`

**Option B — Model-based (if using ensemble):**
- If the model is a Random Forest or Gradient Boosting, use individual tree predictions
- Compute std across tree predictions
- Confidence range = `[prediction - 2*std, prediction + 2*std]`

**Option C — Residual-based:**
- Compute residuals on training set (actual - predicted)
- Group residuals by zipcode or price range
- Use the residual percentiles (5th, 95th) as the interval width

## Files to Modify/Create

- `src/services/predictor.py` — add confidence calculation to `predict()` method
- `src/services/confidence.py` — new: confidence estimation logic (if separating concerns)
- `src/api/endpoints.py` — update response to include `confidence_range`
- `test/unit/test_api_unit.py` — add tests for the new field
