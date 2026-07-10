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
    """Invalid zipcode not in demographics data must return 400 with detail message."""
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


def test_negative_bedrooms_returns_422(test_client):
    """Negative bedrooms must be rejected with a 422."""
    response = test_client.post(
        "/predict",
        json={"zipcode": "98042", "bedrooms": -3},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


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
