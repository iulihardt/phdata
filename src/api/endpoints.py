import json
import pickle
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class HomeFeatures(BaseModel):
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft_living: Optional[float] = None
    sqft_lot: Optional[float] = None
    floors: Optional[float] = None
    sqft_above: Optional[float] = None
    sqft_basement: Optional[float] = None
    zipcode: str


@router.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    Returns 200 if API is ready to accept requests.
    """
    return {"status": "healthy"}


@router.post("/predict")
async def predict(home_features: HomeFeatures, request: Request):
    # Load the model and features
    with open("model/model.pkl", "rb") as model_file:
        model = pickle.load(model_file)

    with open("model/model_features.json") as features_file:
        model_features = json.load(features_file)

    input_data = pd.DataFrame([home_features.dict()])

    # Impute any missing numeric home feature values before further processing
    input_data = request.app.state.imputer.impute(input_data)

    # Load demographic data and merge on zipcode
    demographics = pd.read_csv("data/zipcode_demographics.csv", dtype={"zipcode": str})
    demographic_info = demographics[
        demographics["zipcode"] == home_features.zipcode
    ].drop(columns="zipcode").reset_index(drop=True)

    input_data = pd.concat([input_data, demographic_info], axis=1)

    # Select model features and predict
    input_data = input_data[model_features]
    prediction = model.predict(input_data)

    return {"predicted_price": prediction[0]}
