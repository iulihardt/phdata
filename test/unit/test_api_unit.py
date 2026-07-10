import pytest


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
