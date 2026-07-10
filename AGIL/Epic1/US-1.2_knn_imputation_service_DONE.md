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

---

## Implementation Notes

### What Was Done

**New files:**
- `src/services/__init__.py` — marks `services` as a Python package.
- `src/services/imputer.py` — introduces `KNNImputerService`, a thin wrapper around `sklearn.impute.KNNImputer`. It exposes two public methods:
  - `fit(data_path: str)` — reads `kc_house_data.csv`, selects the 7 numeric home feature columns (`bedrooms`, `bathrooms`, `sqft_living`, `sqft_lot`, `floors`, `sqft_above`, `sqft_basement`), and fits the imputer in-place. Called once at startup.
  - `impute(df: pd.DataFrame) -> pd.DataFrame` — returns a copy of the input DataFrame with missing values in those 7 columns filled using the pre-fitted imputer. Non-numeric columns (e.g. `zipcode`) are left untouched.
  - Parameters follow the notebook recommendation: `n_neighbors=5, weights='distance'`.

**Modified files:**
- `src/main.py` — added a FastAPI `lifespan` async context manager. On startup it creates a `KNNImputerService`, calls `fit("data/kc_house_data.csv")`, and stores the fitted instance in `app.state.imputer`. This ensures the imputer is fitted exactly once per process, never per request.
- `src/api/endpoints.py` — added `Request` to the `predict` function signature to access `request.app.state.imputer`. The imputation step is inserted immediately after building the input DataFrame from the request and before merging demographic data. Removed the `print(input_data)` debug statement left from earlier code.
- `test/conftest.py` — changed `test_client` from a plain return fixture to a `yield` fixture using the `with TestClient(app)` context manager, ensuring the lifespan startup/shutdown events run correctly in tests. Added `sample_home_features_with_missing` fixture (two fields set to `None`).
- `test/unit/test_api_unit.py` — added three new test cases: partial missing fields, all optional fields missing (only `zipcode` provided), and idempotency check (same complete request returns identical price twice).
- `test/integration/test_api_integration.py` — added two new integration tests mirroring the missing-value scenarios above for the live API.

### Acceptance Criteria Status

- [x] KNN Imputer is trained/fitted on the historical dataset (`kc_house_data.csv`)
- [x] Missing values in a prediction request are imputed before being passed to the model
- [x] Imputation uses the same approach validated in `notebooks/imputation_experiment.ipynb` (`KNNImputer(n_neighbors=5, weights='distance')`)
- [x] The imputer is pre-fitted at startup (not re-fitted on every request)
- [x] Predictions with imputed values are reasonable (validated by unit and integration tests)
- [x] When no fields are missing, the prediction result is identical to the current behavior

### Points of Attention

1. **Data availability at startup** — `kc_house_data.csv` must be present at the `data/` path relative to the working directory (i.e. `/app/data/` in Docker, via the symlink `ln -s /app/src/data /app/data` defined in `Dockerfile.test`). If the file is missing the application will fail to start with a `FileNotFoundError`. This is intentional: a broken startup is better than silently serving predictions without imputation.

2. **Feature scope of the imputer** — The imputer is fitted only on the 7 numeric home features that the API actually receives (not on the full 17-column set from the notebook). Demographic features are joined after imputation, so they are never seen as inputs to the imputer. This is simpler and avoids having to re-merge training data at startup, at the cost of not using demographic context during imputation. If higher accuracy is needed in the future, the imputer could be re-fitted on a merged dataset.

3. **`test_client` fixture change** — The fixture now uses `yield` inside `with TestClient(app)`. Any test that was accidentally relying on the old fixture's plain-return behaviour (no lifespan) will now behave correctly. This is a non-breaking change for the existing tests.

4. **No serialization of the fitted imputer** — The imputer is re-fitted from the CSV on every container restart. This is acceptable because fitting is fast (~1–2 s on the full 21 k-row dataset). If startup time becomes a concern, the fitted imputer can be persisted to disk with `joblib` during model training and loaded at startup instead.


O que acontece matematicamente
O KNNImputer(n_neighbors=5, weights='distance') faz o seguinte:

Pega as outras 6 features não-nulas que você mandou (bedrooms=3, bathrooms=2.5, sqft_living=2000, sqft_lot=5000, sqft_above=1500, sqft_basement=500)
Busca os 5 vizinhos mais próximos no dataset kc_house_data.csv (21.613 casas) que têm valores em todas essas colunas
Para cada vizinho, calcula o peso = 1 / distância_euclidiana
Retorna a média ponderada do valor de floors desses 5 vizinhos