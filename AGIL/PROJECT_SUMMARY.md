# Project Summary

## Context

Sound Realty is a real estate company operating in the Seattle area. They use a machine learning model deployed as a REST API (FastAPI + Docker) to estimate property values based on home features and zipcode demographics.

## Current System

- **API**: FastAPI service with a `/predict` endpoint that accepts home features (bedrooms, bathrooms, sqft_living, sqft_lot, floors, sqft_above, sqft_basement, zipcode) and returns a predicted price.
- **Model**: Pre-trained ML model (`model.pkl`) with feature metadata (`model_features.json`).
- **Data**: Historical sales data, zipcode demographics CSV, and unseen test examples for validation.
- **Infrastructure**: Dockerized deployment with unit and integration test support via `docker-compose`.

## Key Problems Identified

1. **No missing data handling**: The API rejects any request with incomplete fields. Real-world property data frequently has gaps.
2. **Performance bottleneck**: The model, feature metadata, and demographics CSV are loaded from disk on every single request instead of being loaded once at startup.
3. **Technical debt**: The `endpoints.py` file does everything inline (loading, processing, predicting), ignores the existing `loader.py` utility, uses `print` instead of logging, and lacks proper error handling.
4. **Insufficient testing**: Current tests don't cover missing data scenarios or performance validation.
5. **Documentation gaps**: README doesn't reflect the imputation capability or performance improvements.

## Tech Stack

- Python 3.x, FastAPI, Pydantic
- scikit-learn (model + KNNImputer)
- pandas, Docker, pytest
