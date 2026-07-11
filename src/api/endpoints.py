import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class HomeFeatures(BaseModel):
    """Property features used to predict home value in the Seattle area."""

    bedrooms: Optional[int] = Field(
        default=None, ge=0,
        description="Number of bedrooms (0 for studios)",
        examples=[3],
    )
    bathrooms: Optional[float] = Field(
        default=None, ge=0,
        description="Number of bathrooms (supports half-baths, e.g. 2.5)",
        examples=[2.5],
    )
    sqft_living: Optional[float] = Field(
        default=None, gt=0,
        description="Interior living area in square feet",
        examples=[2000.0],
    )
    sqft_lot: Optional[float] = Field(
        default=None, gt=0,
        description="Total lot size in square feet",
        examples=[5000.0],
    )
    floors: Optional[float] = Field(
        default=None, gt=0,
        description="Number of floors (supports half-floors, e.g. 1.5)",
        examples=[2.0],
    )
    sqft_above: Optional[float] = Field(
        default=None, ge=0,
        description="Above-ground living area in square feet",
        examples=[1500.0],
    )
    sqft_basement: Optional[float] = Field(
        default=None, ge=0,
        description="Basement area in square feet (0 if no basement)",
        examples=[500.0],
    )
    zipcode: str = Field(
        ...,
        pattern=r"^\d{5}$",
        description="5-digit US zipcode (always required)",
        examples=["98125"],
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}


@router.post("/predict")
async def predict(home_features: HomeFeatures, request: Request):
    """Accept home features and return a predicted price."""
    prediction_service = request.app.state.prediction_service

    data = home_features.model_dump()
    has_missing = any(v is None for k, v in data.items() if k != "zipcode")

    try:
        price = prediction_service.predict(
            home_data=data,
            zipcode=home_features.zipcode,
        )
    except ValueError as exc:
        logger.warning("Prediction failed for zipcode=%s: %s", home_features.zipcode, exc)
        raise HTTPException(status_code=400, detail="zipcode not found") from exc

    logger.info(
        "Prediction complete: zipcode=%s imputation_used=%s predicted_price=%.2f",
        home_features.zipcode,
        has_missing,
        price,
    )
    return {"predicted_price": price}
