# US-1.2 — KNN Imputation Service + Pipeline Integration

**Epic**: E1 — Missing Data Handling (KNN Imputation)
**Priority**: Must | **Story Points**: 5

## User Story

As the system, I want to automatically fill in missing property values using KNN imputation before making a prediction, so that users receive accurate estimates even with incomplete data.

## Acceptance Criteria

- [ ] KNN Imputer is trained/fitted on the historical dataset (`kc_house_data.csv`)
- [ ] Missing values in a prediction request are imputed before being passed to the model
- [ ] Imputation uses the same approach validated in `notebooks/imputation_experiment.ipynb`
- [ ] The imputer is pre-fitted at startup (not re-fitted on every request)
- [ ] Predictions with imputed values are reasonable (validated against known examples)
- [ ] When no fields are missing, the prediction result is identical to the current behavior

## Technical Notes

- Review `notebooks/imputation_experiment.ipynb` for the researched approach
- Use `sklearn.impute.KNNImputer`
- Create a new service/module (e.g., `src/services/imputer.py`) to encapsulate imputation logic
- The imputer should be fitted on the numeric feature columns from `kc_house_data.csv`
- Integration point: after receiving the request and before calling `model.predict()`
- Pipeline flow: Request -> Nullable parse -> Merge demographics -> Impute missing -> Select features -> Predict

## Files to Create/Modify

- `src/services/imputer.py` — new: imputation service
- `src/api/endpoints.py` — integrate imputation into predict flow
- `src/utils/loader.py` — add imputer loading if needed
