import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_BATCH_SIZE = 100


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


class BatchRequest(BaseModel):
    """Batch of property feature payloads for portfolio-style prediction."""

    properties: list[dict[str, Any]] = Field(
        ...,
        description="List of home feature objects (same schema as /predict)",
        examples=[
            [
                {
                    "bedrooms": 3,
                    "bathrooms": 2.5,
                    "sqft_living": 2000,
                    "sqft_lot": 5000,
                    "floors": 2,
                    "sqft_above": 1500,
                    "sqft_basement": 500,
                    "zipcode": "98125",
                },
                {
                    "bedrooms": None,
                    "bathrooms": 1.0,
                    "sqft_living": 1200,
                    "sqft_lot": None,
                    "floors": 1,
                    "sqft_above": 1200,
                    "sqft_basement": 0,
                    "zipcode": "98042",
                },
            ]
        ],
    )


class BatchPredictionItem(BaseModel):
    index: int
    predicted_price: Optional[float] = None
    status: str
    error: Optional[str] = None


class BatchResponse(BaseModel):
    predictions: list[BatchPredictionItem]
    total: int
    successful: int
    failed: int


def _format_validation_error(exc: ValidationError) -> str:
    """Format a Pydantic ValidationError like the single-/predict 422 detail."""
    parts = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"])
        parts.append(f"{field}: {err['msg']}")
    return "; ".join(parts)


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


@router.post("/predict/batch", response_model=BatchResponse)
async def predict_batch(batch: BatchRequest, request: Request):
    """
    Predict prices for multiple properties in one request.

    Invalid items (schema or unknown zipcode) return per-item errors without
    failing the whole batch. Empty batches return an empty result set.
    """
    if len(batch.properties) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(batch.properties)} exceeds maximum of {MAX_BATCH_SIZE}",
        )

    prediction_service = request.app.state.prediction_service

    results: list[dict] = [None] * len(batch.properties)  # type: ignore[list-item]
    valid_rows: list[tuple[int, dict]] = []

    for idx, raw in enumerate(batch.properties):
        try:
            features = HomeFeatures.model_validate(raw)
        except ValidationError as exc:
            results[idx] = {
                "index": idx,
                "predicted_price": None,
                "status": "error",
                "error": _format_validation_error(exc),
            }
            continue
        valid_rows.append((idx, features.model_dump()))

    if valid_rows:
        batch_results = prediction_service.predict_batch(
            [row for _, row in valid_rows]
        )
        for (orig_idx, _), item in zip(valid_rows, batch_results):
            item["index"] = orig_idx
            results[orig_idx] = item

    successful = sum(1 for r in results if r and r["status"] == "success")
    failed = len(results) - successful

    logger.info(
        "Batch prediction complete: total=%d successful=%d failed=%d",
        len(results),
        successful,
        failed,
    )

    return {
        "predictions": results,
        "total": len(results),
        "successful": successful,
        "failed": failed,
    }
