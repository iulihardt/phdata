import csv

import pytest
from unittest.mock import patch

from src.services.imputer import NUMERIC_HOME_FEATURES


# ---- Helpers ----


def _load_unseen_examples():
    """Load future_unseen_examples.csv and yield (row_index, payload_dict) tuples."""
    with open("src/data/future_unseen_examples.csv") as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader):
            yield pytest.param(
                {
                    "bedrooms": int(row["bedrooms"]),
                    "bathrooms": float(row["bathrooms"]),
                    "sqft_living": float(row["sqft_living"]),
                    "sqft_lot": float(row["sqft_lot"]),
                    "floors": float(row["floors"]),
                    "sqft_above": float(row["sqft_above"]),
                    "sqft_basement": float(row["sqft_basement"]),
                    "zipcode": str(row["zipcode"]),
                },
                id=f"row-{idx}-zip-{row['zipcode']}",
            )


UNSEEN_EXAMPLES = list(_load_unseen_examples())

MIN_REASONABLE_PRICE = 50_000.0
MAX_REASONABLE_PRICE = 5_000_000.0


# ---- Core Endpoint Tests ----


def test_health_endpoint(test_client):
    """Test the /health endpoint returns correct status."""
    response = test_client.get("/health")
    assert response.status_code == 200
    response_data = response.json()
    assert "status" in response_data
    assert response_data["status"] == "healthy"


def test_predict_endpoint_valid_input(test_client, sample_home_features):
    """Test the /predict endpoint with a complete (no missing values) payload."""
    response = test_client.post("/predict", json=sample_home_features)
    assert response.status_code == 200
    response_data = response.json()
    assert "predicted_price" in response_data
    assert isinstance(response_data["predicted_price"], float)


def test_predict_with_missing_values(test_client, sample_home_features_with_missing):
    """Test that KNN imputation fills missing fields and the request succeeds."""
    response = test_client.post("/predict", json=sample_home_features_with_missing)
    assert response.status_code == 200
    response_data = response.json()
    assert "predicted_price" in response_data
    assert isinstance(response_data["predicted_price"], float)
    assert response_data["predicted_price"] > 0


def test_predict_only_zipcode_required(test_client):
    """Test that a request with all optional fields missing still returns a prediction."""
    response = test_client.post("/predict", json={"zipcode": "98042"})
    assert response.status_code == 200
    response_data = response.json()
    assert "predicted_price" in response_data
    assert response_data["predicted_price"] > 0


def test_predict_consistent_without_missing(test_client, sample_home_features):
    """Test that two identical complete requests return the same prediction."""
    response1 = test_client.post("/predict", json=sample_home_features)
    response2 = test_client.post("/predict", json=sample_home_features)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["predicted_price"] == response2.json()["predicted_price"]


# ---- US-4.1: Single Missing Field ----


@pytest.mark.parametrize("missing_field", NUMERIC_HOME_FEATURES)
def test_predict_single_missing_field(test_client, sample_home_features, missing_field):
    """Each numeric field can be individually null and still produce a valid prediction."""
    payload = {**sample_home_features, missing_field: None}
    response = test_client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_price"] > 0


# ---- US-4.1: Imputed vs Full-Data Reasonableness ----


def test_imputed_prediction_within_50pct_of_full(test_client, sample_home_features):
    """A prediction with 2 missing fields should be within 50% of the full-data prediction."""
    full_resp = test_client.post("/predict", json=sample_home_features)
    full_price = full_resp.json()["predicted_price"]

    partial = {**sample_home_features, "bathrooms": None, "sqft_lot": None}
    partial_resp = test_client.post("/predict", json=partial)
    partial_price = partial_resp.json()["predicted_price"]

    assert partial_price > 0
    ratio = partial_price / full_price
    assert 0.5 <= ratio <= 1.5, (
        f"Imputed price ${partial_price:,.0f} is too far from full price ${full_price:,.0f} (ratio={ratio:.2f})"
    )


# ---- US-4.1: future_unseen_examples.csv Validation ----


@pytest.mark.parametrize("payload", UNSEEN_EXAMPLES)
def test_unseen_example_returns_valid_prediction(test_client, payload):
    """Every row from future_unseen_examples.csv should produce a prediction in a reasonable range."""
    response = test_client.post("/predict", json=payload)
    assert response.status_code == 200
    price = response.json()["predicted_price"]
    assert MIN_REASONABLE_PRICE <= price <= MAX_REASONABLE_PRICE, (
        f"Price ${price:,.0f} outside reasonable range for zipcode {payload['zipcode']}"
    )


# --- Edge Case Tests (US-1.3) ---


def test_invalid_zipcode_returns_400(test_client):
    """Valid 5-digit zipcode not in demographics data must return 400."""
    response = test_client.post("/predict", json={"zipcode": "00000"})
    assert response.status_code == 400
    assert response.json() == {"detail": "zipcode not found"}


def test_negative_sqft_living_returns_422(test_client):
    """Negative sqft_living must be rejected with 422 and a field-level error."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "sqft_living": -100.0},
    )
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    fields = [e["field"] for e in body["detail"]]
    assert "sqft_living" in fields


def test_negative_bedrooms_returns_422(test_client):
    """Negative bedrooms must be rejected with a 422."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "bedrooms": -3},
    )
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    fields = [e["field"] for e in body["detail"]]
    assert "bedrooms" in fields


def test_invalid_type_returns_422(test_client):
    """String value where a number is expected must return 422 with field-level errors."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "sqft_living": "big house"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_empty_body_returns_422(test_client):
    """Empty request body must return 422 because zipcode is required."""
    response = test_client.post("/predict", json={})
    assert response.status_code == 422
    assert "detail" in response.json()


# --- Input Validation Tests (US-3.2) ---


def test_zipcode_format_letters_returns_422(test_client):
    """Non-numeric zipcode must be rejected."""
    response = test_client.post("/predict", json={"zipcode": "abcde"})
    assert response.status_code == 422
    body = response.json()
    fields = [e["field"] for e in body["detail"]]
    assert "zipcode" in fields


def test_zipcode_format_too_short_returns_422(test_client):
    """Zipcode with fewer than 5 digits must be rejected."""
    response = test_client.post("/predict", json={"zipcode": "9812"})
    assert response.status_code == 422
    body = response.json()
    fields = [e["field"] for e in body["detail"]]
    assert "zipcode" in fields


def test_zipcode_format_too_long_returns_422(test_client):
    """Zipcode with more than 5 digits must be rejected."""
    response = test_client.post("/predict", json={"zipcode": "981250"})
    assert response.status_code == 422
    body = response.json()
    fields = [e["field"] for e in body["detail"]]
    assert "zipcode" in fields


def test_zero_sqft_living_returns_422(test_client):
    """Zero sqft_living must be rejected (gt=0 constraint)."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "sqft_living": 0},
    )
    assert response.status_code == 422
    body = response.json()
    fields = [e["field"] for e in body["detail"]]
    assert "sqft_living" in fields


def test_zero_floors_returns_422(test_client):
    """Zero floors must be rejected (gt=0 constraint)."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "floors": 0},
    )
    assert response.status_code == 422
    body = response.json()
    fields = [e["field"] for e in body["detail"]]
    assert "floors" in fields


def test_zero_bedrooms_accepted(test_client):
    """Zero bedrooms is valid (studio apartments)."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "bedrooms": 0},
    )
    assert response.status_code == 200


def test_zero_sqft_basement_accepted(test_client):
    """Zero sqft_basement is valid (no basement)."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "sqft_basement": 0},
    )
    assert response.status_code == 200


def test_validation_error_format_is_consistent(test_client):
    """Every validation error entry must have 'field' and 'message' keys."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "bedrooms": -1, "sqft_living": -50},
    )
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)
    for entry in body["detail"]:
        assert "field" in entry
        assert "message" in entry


def test_multiple_validation_errors_returned(test_client):
    """Multiple invalid fields should produce multiple error entries."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "bedrooms": -1, "sqft_living": -50},
    )
    assert response.status_code == 422
    body = response.json()
    assert len(body["detail"]) >= 2
    fields = {e["field"] for e in body["detail"]}
    assert "bedrooms" in fields
    assert "sqft_living" in fields


# --- Logging & Error Handling Tests (US-3.3) ---


def test_unhandled_exception_returns_json_500(test_client):
    """An unexpected exception must return a clean JSON 500, not an HTML traceback."""
    with patch(
        "services.predictor.PredictionService.predict",
        side_effect=RuntimeError("unexpected failure"),
    ):
        response = test_client.post("/predict", json={"zipcode": "98042"})
    assert response.status_code == 500
    body = response.json()
    assert body == {"detail": "Internal server error"}


def test_unhandled_exception_does_not_leak_traceback(test_client):
    """The 500 response body must not contain Python traceback information."""
    with patch(
        "services.predictor.PredictionService.predict",
        side_effect=TypeError("NoneType object is not iterable"),
    ):
        response = test_client.post("/predict", json={"zipcode": "98042"})
    assert response.status_code == 500
    body = response.json()
    assert "Traceback" not in str(body)
    assert "NoneType" not in str(body)


def test_predict_logs_imputation_used(test_client, sample_home_features_with_missing, caplog):
    """When imputation is triggered, the log must indicate imputation_used=True."""
    import logging
    with caplog.at_level(logging.INFO, logger="api.endpoints"):
        test_client.post("/predict", json=sample_home_features_with_missing)
    assert any("imputation_used=True" in record.message for record in caplog.records)


def test_predict_logs_no_imputation(test_client, sample_home_features, caplog):
    """When all fields are provided, the log must indicate imputation_used=False."""
    import logging
    with caplog.at_level(logging.INFO, logger="api.endpoints"):
        test_client.post("/predict", json=sample_home_features)
    assert any("imputation_used=False" in record.message for record in caplog.records)
