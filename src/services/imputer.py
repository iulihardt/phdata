import pandas as pd
from sklearn.impute import KNNImputer

NUMERIC_HOME_FEATURES = [
    "bedrooms",
    "bathrooms",
    "sqft_living",
    "sqft_lot",
    "floors",
    "sqft_above",
    "sqft_basement",
]


class KNNImputerService:
    """
    Wraps sklearn KNNImputer to handle missing home feature values.

    The imputer is fitted once at application startup on the historical
    sales dataset. At inference time it transforms only the numeric home
    feature columns, leaving all other columns (e.g. zipcode) untouched.

    Parameters mirror the approach validated in notebooks/imputation_experiment.ipynb:
      - n_neighbors=5
      - weights='distance'  (closer neighbours contribute more)
    """

    def __init__(self, n_neighbors: int = 5, weights: str = "distance") -> None:
        self._imputer = KNNImputer(n_neighbors=n_neighbors, weights=weights)
        self._fitted = False

    def fit(self, data_path: str) -> None:
        """Fit the imputer on the numeric home feature columns of the training dataset."""
        df = pd.read_csv(data_path, usecols=NUMERIC_HOME_FEATURES)
        self._imputer.fit(df)
        self._fitted = True

    def impute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a copy of *df* with missing values in NUMERIC_HOME_FEATURES filled.

        Columns not in NUMERIC_HOME_FEATURES are passed through unchanged.
        """
        if not self._fitted:
            raise RuntimeError(
                "KNNImputerService must be fitted before calling impute(). "
                "Call fit() during application startup."
            )
        result = df.copy()
        result[NUMERIC_HOME_FEATURES] = self._imputer.transform(
            result[NUMERIC_HOME_FEATURES]
        )
        return result
