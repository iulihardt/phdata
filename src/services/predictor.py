from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from services.imputer import KNNImputerService

logger = logging.getLogger(__name__)


class PredictionService:
    """Orchestrates the full prediction pipeline: imputation → demographics → prediction."""

    def __init__(
        self,
        model: Any,
        model_features: list[str],
        demographics: pd.DataFrame,
        imputer: KNNImputerService,
    ) -> None:
        self._model = model
        self._model_features = model_features
        self._demographics = demographics
        self._imputer = imputer

    def predict(self, home_data: dict, zipcode: str) -> float:
        """
        Run the full prediction pipeline for a single home.

        Raises ValueError if the zipcode is not found in demographics data.
        """
        input_data = pd.DataFrame([home_data])

        input_data = self._imputer.impute(input_data)

        demographic_info = (
            self._demographics[self._demographics["zipcode"] == zipcode]
            .drop(columns="zipcode")
            .reset_index(drop=True)
        )

        if demographic_info.empty:
            raise ValueError(f"zipcode '{zipcode}' not found in demographics data")

        input_data = pd.concat([input_data, demographic_info], axis=1)
        input_data = input_data[self._model_features]

        prediction = self._model.predict(input_data)
        return float(prediction[0])

    def predict_batch(self, properties: list[dict]) -> list[dict]:
        """
        Run the prediction pipeline for multiple homes in one pass.

        Vectorizes imputation and model.predict. Items with unknown zipcodes
        are returned as per-item errors without aborting the batch.

        Returns a list of dicts in input order:
          {index, predicted_price, status} or
          {index, predicted_price: None, status: "error", error: str}
        """
        if not properties:
            return []

        results: list[dict | None] = [None] * len(properties)
        df = pd.DataFrame(properties)
        df = self._imputer.impute(df)

        merged = df.merge(
            self._demographics, on="zipcode", how="left", indicator=True
        )
        missing_zip_mask = merged["_merge"] == "left_only"

        for idx in merged.index[missing_zip_mask]:
            results[int(idx)] = {
                "index": int(idx),
                "predicted_price": None,
                "status": "error",
                "error": "zipcode not found",
            }

        valid_mask = ~missing_zip_mask
        if valid_mask.any():
            valid = merged.loc[valid_mask, self._model_features]
            prices = self._model.predict(valid)
            for row_pos, price in zip(merged.index[valid_mask], prices):
                results[int(row_pos)] = {
                    "index": int(row_pos),
                    "predicted_price": float(price),
                    "status": "success",
                }

        return results  # type: ignore[return-value]
