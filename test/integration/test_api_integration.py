import pytest

from src.services.imputer import NUMERIC_HOME_FEATURES


@pytest.mark.integration
def test_predict_endpoint_integration(http_client, sample_home_features):
    """Test the /predict endpoint via HTTP using httpx client."""
    response = http_client.post("/predict", json=sample_home_features)
    assert response.status_code == 200
    response_data = response.json()
    assert "predicted_price" in response_data
    assert isinstance(response_data["predicted_price"], float)
    assert response_data["predicted_price"] > 0


@pytest.mark.integration
def test_predict_with_missing_values_integration(http_client, sample_home_features_with_missing):
    """Test that the live API handles missing values via KNN imputation."""
    response = http_client.post("/predict", json=sample_home_features_with_missing)
    assert response.status_code == 200
    response_data = response.json()
    assert "predicted_price" in response_data
    assert response_data["predicted_price"] > 0


@pytest.mark.integration
def test_predict_only_zipcode_integration(http_client):
    """Test that the live API handles a request with only zipcode provided."""
    response = http_client.post("/predict", json={"zipcode": "98042"})
    assert response.status_code == 200
    response_data = response.json()
    assert "predicted_price" in response_data
    assert response_data["predicted_price"] > 0


@pytest.mark.integration
def test_health_endpoint_integration(http_client):
    """Test the /health endpoint via HTTP using httpx client."""
    response = http_client.get("/health")
    assert response.status_code == 200
    response_data = response.json()
    assert "status" in response_data
    assert response_data["status"] == "healthy"


# ---- US-4.1: Missing Data Edge Cases (Integration) ----


@pytest.mark.integration
@pytest.mark.parametrize("missing_field", NUMERIC_HOME_FEATURES)
def test_single_missing_field_integration(http_client, sample_home_features, missing_field):
    """Each numeric field can be individually null via the live API."""
    payload = {**sample_home_features, missing_field: None}
    response = http_client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["predicted_price"] > 0


@pytest.mark.integration
def test_invalid_zipcode_returns_400_integration(http_client):
    """A valid-format zipcode not in demographics must return 400 from the live API."""
    response = http_client.post("/predict", json={"zipcode": "00000"})
    assert response.status_code == 400


@pytest.mark.integration
def test_imputed_vs_full_prediction_reasonableness_integration(http_client, sample_home_features):
    """Imputed prediction should be within 50% of full-data prediction via live API."""
    full_resp = http_client.post("/predict", json=sample_home_features)
    full_price = full_resp.json()["predicted_price"]

    partial = {**sample_home_features, "bathrooms": None, "sqft_lot": None}
    partial_resp = http_client.post("/predict", json=partial)
    partial_price = partial_resp.json()["predicted_price"]

    ratio = partial_price / full_price
    assert 0.5 <= ratio <= 1.5
