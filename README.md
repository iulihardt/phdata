# Sound Realty — Home Price Prediction API

A production-oriented RESTful API (FastAPI + Docker) that estimates home values in the
Seattle / King County area. The service wraps a pre-trained scikit-learn model
(`KNeighborsRegressor` + `RobustScaler`) and adds the capabilities needed to run it
reliably against real-world, often-incomplete data:

- **Missing-data handling** via KNN imputation — clients can omit any numeric field.
- **Single and batch prediction** endpoints.
- **Startup preloading** of all resources — zero disk I/O per request.
- **Input validation** with clear, consistent error messages and auto-generated Swagger docs.
- **Structured logging** and global error handling for production observability.
- **Interactive map UI** (`/directmap`) to estimate prices by clicking a location.

## What's Implemented

The work is tracked as user stories under `AGIL/`. The following are delivered and running:

| Area | Capability | Story |
|------|-----------|-------|
| Missing data | Nullable schema (all fields optional except `zipcode`) | US-1.1 |
| Missing data | KNN imputation service, fitted at startup | US-1.2 |
| Missing data | Edge-case handling (invalid zipcode, all-nulls, bad types) | US-1.3 |
| Performance | Model, features, demographics & imputer preloaded once at startup | US-2.1 |
| Code quality | Refactor into `services/` layer, pinned dependencies | US-3.1 |
| Code quality | Declarative Pydantic validation + Swagger constraints/examples | US-3.2 |
| Code quality | Structured logging + global exception handling | US-3.3 |
| Value-add | Interactive map page + reverse geocoding | US-6.1 |
| Value-add | Batch prediction endpoint (`/predict/batch`) | US-6.3 |

A latency benchmark script is also included (`test/benchmark_api.py`), see [Benchmark](#benchmark).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check for container orchestration |
| `POST` | `/predict` | Predict the price of a single property |
| `POST` | `/predict/batch` | Predict prices for up to 100 properties in one request |
| `GET`  | `/directmap` | Interactive Leaflet map UI for point-and-click estimation |
| `GET`  | `/reverse-geocode` | Resolve a lat/lon into ZIP / city / state (Nominatim proxy) |
| `GET`  | `/docs` | Interactive OpenAPI (Swagger) documentation |

## Project Structure

```
phdata-mle-project-challenge-2026
├── src
│   ├── main.py                     # App wiring: lifespan preloading, logging, error handlers, CORS, routers
│   ├── api
│   │   ├── endpoints.py            # HTTP layer: /health, /predict, /predict/batch + Pydantic models
│   │   └── web.py                  # HTTP layer: /directmap, /reverse-geocode
│   ├── services
│   │   ├── imputer.py              # KNNImputerService (KNN imputation of missing features)
│   │   └── predictor.py            # PredictionService (impute → merge demographics → predict)
│   ├── utils
│   │   └── loader.py               # Resource loaders (model, features, demographics)
│   ├── templates
│   │   └── directmap.html          # Jinja2 template for the map UI
│   ├── static
│   │   ├── css/directmap.css       # Map UI styles
│   │   └── js/directmap.js         # Leaflet map, geocoding, debounced prediction
│   ├── model
│   │   ├── create_model.py         # Trains the model and exports artifacts
│   │   ├── Dockerfile              # Image used to (re)generate model artifacts
│   │   ├── model.pkl               # Serialized ML model (generated)
│   │   └── model_features.json     # Feature order expected by the model (generated)
│   └── data
│       ├── kc_house_data.csv       # Historical sales (used to fit the imputer)
│       ├── zipcode_demographics.csv# Demographic features joined at prediction time
│       └── future_unseen_examples.csv
├── test
│   ├── unit/                       # In-process TestClient tests (fast)
│   ├── integration/                # Tests against a live API container
│   ├── conftest.py                 # Shared fixtures
│   └── benchmark_api.py            # Latency/throughput benchmark script
├── requirements.txt                # Runtime dependencies (pinned)
├── requirements-test.txt           # Test-only dependencies
├── Dockerfile                      # API image
├── Dockerfile.test                 # Test image
├── docker-compose.test.yml         # Integration test orchestration
├── Makefile                        # Test shortcuts
└── README.md
```

## Setup Instructions

### Prerequisites

- Docker installed and running
- Git (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd phdata-mle-project-challenge-2026
```

### Step 2: Generate Model Artifacts (First Time Only)

The API needs `model.pkl` and `model_features.json` in `src/model/`. These are produced by
the training script. This step only needs to be run once (or whenever you want to retrain).

**Build the model-creation image:**
```bash
docker build -f src/model/Dockerfile -t create-model .
```

**Run the container to generate the artifacts:**
```bash
docker run --rm -v "$(pwd)/src/model:/app/model" create-model
```

### Step 3: Build and Run the API

**Build the API image:**
```bash
docker build -t phdata-mle-api .
```

**Run the API container:**
```bash
docker run -d -p 8000:8000 --name housing-api phdata-mle-api
```

### Step 4: Access the API

- Interactive docs (Swagger): `http://127.0.0.1:8000/docs`
- Interactive map UI: `http://127.0.0.1:8000/directmap`
- Health check: `http://127.0.0.1:8000/health`

### Managing the Container

```bash
docker stop housing-api      # Stop
docker start housing-api     # Start again
docker rm housing-api        # Remove
docker logs housing-api      # View logs (includes startup resource-loading messages)
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

Example:
```bash
docker run -d -p 8000:8000 -e LOG_LEVEL=DEBUG --name housing-api phdata-mle-api
```

## Usage

### Single prediction — `POST /predict`

Send home features as JSON. Any numeric field may be `null` (or omitted) — KNN imputation
fills the gaps before prediction. `zipcode` is always required and must be a 5-digit string.

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "bedrooms": 3,
    "bathrooms": 2.5,
    "sqft_living": 2000,
    "sqft_lot": 5000,
    "floors": 2,
    "sqft_above": 1500,
    "sqft_basement": 500,
    "zipcode": "98125"
  }'
```

Response:
```json
{"predicted_price": 450000.0}
```

**Error behavior:**
- Malformed input (negative values, non-numeric types, bad zipcode format) → `422` with
  `{"detail": [{"field": "...", "message": "..."}]}`.
- Valid-format zipcode not in the coverage area → `400` with `{"detail": "zipcode not found"}`.

### Batch prediction — `POST /predict/batch`

Submit multiple properties in one request (max **100** items). Results keep the input order.
Invalid items return per-item errors without failing the whole batch; an empty list returns an
empty result.

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
      }
    ]
  }'
```

Response shape:
```json
{
  "predictions": [
    {"index": 0, "predicted_price": 450000.0, "status": "success", "error": null},
    {"index": 1, "predicted_price": 285000.0, "status": "success", "error": null}
  ],
  "total": 2,
  "successful": 2,
  "failed": 0
}
```

A failed item looks like:
```json
{"index": 1, "predicted_price": null, "status": "error", "error": "zipcode not found"}
```

### Interactive map — `GET /directmap`

Open `http://127.0.0.1:8000/directmap` in a browser. Click (or drag the marker) anywhere on the
map to set a location; the ZIP code is resolved automatically via reverse geocoding and the price
prediction updates in real time as you adjust the property sliders (no "Predict" button needed).

> Notes:
> - The model only covers King County (Seattle-area) ZIP codes. Clicks outside this region show a
>   clear "ZIP code not supported" message.
> - Reverse geocoding proxies the free Nominatim/OpenStreetMap service, so the container needs
>   outbound internet access for the map page to resolve ZIP codes.

## How Prediction Works

1. The request payload is validated against the `HomeFeatures` schema.
2. Missing numeric features are filled by a `KNNImputer(n_neighbors=5, weights="distance")`
   fitted once at startup on `kc_house_data.csv`.
3. Demographic features for the property's ZIP code are joined from `zipcode_demographics.csv`.
4. Columns are ordered to match `model_features.json` and passed to the model for prediction.

All resources (model, feature list, demographics, fitted imputer) are loaded **once at startup**
and held in memory, so requests incur no disk I/O.

## Testing

The project uses Docker-based testing for environment parity between development and production.

### Quick Start

```bash
make test-unit          # Fast, in-process unit tests
make test-integration   # Full-environment integration tests (Docker Compose)
make test-all           # Both suites
make clean              # Remove test containers and artifacts
```

### Test Types

**Unit Tests** (`test/unit/`)
- Use FastAPI `TestClient` for in-process testing (no external containers).
- Fast execution; ideal for rapid iteration.
- Cover prediction happy paths, imputation, edge cases, validation, batch behavior,
  the map page, and reverse geocoding (external services mocked).

**Integration Tests** (`test/integration/`)
- Run against a real API container brought up via `docker-compose.test.yml`.
- Verify end-to-end behavior over HTTP, including Docker networking and health checks.

### Coverage Reports

After running tests, an HTML coverage report is generated under `test-results/`:
```bash
open test-results/coverage/index.html
```
A terminal coverage summary is also printed after each run.

### Running Specific Tests

```bash
# A specific file
docker run --rm ml-api-test pytest test/unit/test_api_unit.py -v

# Tests matching a pattern
docker run --rm ml-api-test pytest -k "batch" -v
```

## Benchmark

`test/benchmark_api.py` sends N requests to `/predict` and reports latency percentiles
(min / mean / p50 / p95 / p99 / max) and throughput. Run it against a running API container:

```bash
# Ensure the API is running on http://localhost:8000, then:
python test/benchmark_api.py -n 100
```

## Troubleshooting

**"Cannot connect to the Docker daemon"** — Ensure Docker is running (`docker ps`).

**Integration tests fail with connection errors** — Check the API container health:
```bash
docker-compose -f docker-compose.test.yml up
docker-compose -f docker-compose.test.yml logs api
```

**"Port 8000 already in use"** — Stop whatever is using the port:
```bash
docker-compose -f docker-compose.test.yml down
docker stop housing-api
```

**Startup fails with `FileNotFoundError`** — The model artifacts and data files must exist.
Confirm `src/model/model.pkl`, `src/model/model_features.json`, and the CSVs in `src/data/`
are present (regenerate the model with the Step 2 commands if needed).

## Feedback

We welcome any feedback regarding the project or the interview process. Your insights are
valuable to us as we strive to improve the experience for future candidates.
