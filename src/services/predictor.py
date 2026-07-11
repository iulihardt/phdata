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
