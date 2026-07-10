from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

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

    @field_validator("bedrooms", "bathrooms", "sqft_living", "sqft_lot", "floors", "sqft_above", "sqft_basement")
    @classmethod
    def must_be_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("must be a non-negative number")
        return v


@router.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    Returns 200 if API is ready to accept requests.
    """
    return {"status": "healthy"}


@router.post("/predict")
async def predict(home_features: HomeFeatures, request: Request):
    state = request.app.state

    input_data = pd.DataFrame([home_features.model_dump()])

    # Impute missing numeric home feature values using the pre-fitted imputer
    input_data = state.imputer.impute(input_data)

    # Look up demographic data from the in-memory DataFrame
    demographic_info = (
        state.demographics[state.demographics["zipcode"] == home_features.zipcode]
        .drop(columns="zipcode")
        .reset_index(drop=True)
    )

    if demographic_info.empty:
        raise HTTPException(status_code=400, detail="zipcode not found")

    input_data = pd.concat([input_data, demographic_info], axis=1)

    # Select model features and predict using the pre-loaded model
    input_data = input_data[state.model_features]
    prediction = state.model.predict(input_data)

    return {"predicted_price": prediction[0]}
