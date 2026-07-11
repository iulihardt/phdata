"""Unit tests for KNNImputerService in isolation (US-4.1)."""

import numpy as np
import pandas as pd
import pytest

from src.services.imputer import NUMERIC_HOME_FEATURES, KNNImputerService

DATA_PATH = "src/data/kc_house_data.csv"


@pytest.fixture(scope="module")
def fitted_imputer() -> KNNImputerService:
    """Provide a KNNImputerService fitted on the real training data."""
    imputer = KNNImputerService()
    imputer.fit(DATA_PATH)
    return imputer


@pytest.fixture(scope="module")
def training_stats() -> dict:
    """Pre-compute min/max for each numeric feature from the training set."""
    df = pd.read_csv(DATA_PATH, usecols=NUMERIC_HOME_FEATURES)
    return {col: {"min": df[col].min(), "max": df[col].max()} for col in NUMERIC_HOME_FEATURES}


@pytest.fixture()
def complete_row() -> dict:
    return {
        "bedrooms": 3,
        "bathrooms": 2.0,
        "sqft_living": 1500.0,
        "sqft_lot": 5000.0,
        "floors": 1.0,
        "sqft_above": 1200.0,
        "sqft_basement": 300.0,
    }


# ---- Core Behaviour ----


class TestImputerNotFitted:
    def test_impute_raises_if_not_fitted(self, complete_row):
        imputer = KNNImputerService()
        df = pd.DataFrame([complete_row])
        with pytest.raises(RuntimeError, match="must be fitted"):
            imputer.impute(df)


class TestImputeCompleteData:
    def test_no_missing_values_passes_through(self, fitted_imputer, complete_row):
        df = pd.DataFrame([complete_row])
        result = fitted_imputer.impute(df)
        pd.testing.assert_frame_equal(result, df, check_dtype=False)


class TestImputeSingleMissing:
    @pytest.mark.parametrize("missing_field", NUMERIC_HOME_FEATURES)
    def test_single_missing_is_filled(self, fitted_imputer, complete_row, missing_field):
        row = {**complete_row, missing_field: np.nan}
        df = pd.DataFrame([row])
        result = fitted_imputer.impute(df)
        assert not result[missing_field].isna().any(), f"{missing_field} still NaN after imputation"

    @pytest.mark.parametrize("missing_field", NUMERIC_HOME_FEATURES)
    def test_single_missing_value_within_training_range(
        self, fitted_imputer, complete_row, missing_field, training_stats
    ):
        row = {**complete_row, missing_field: np.nan}
        df = pd.DataFrame([row])
        result = fitted_imputer.impute(df)
        imputed = result[missing_field].iloc[0]
        stats = training_stats[missing_field]
        assert stats["min"] <= imputed <= stats["max"], (
            f"{missing_field}={imputed} outside training range [{stats['min']}, {stats['max']}]"
        )


class TestImputeMultipleMissing:
    def test_multiple_missing_are_filled(self, fitted_imputer, complete_row):
        row = {**complete_row, "bathrooms": np.nan, "sqft_living": np.nan, "sqft_lot": np.nan}
        df = pd.DataFrame([row])
        result = fitted_imputer.impute(df)
        for field in ("bathrooms", "sqft_living", "sqft_lot"):
            assert not np.isnan(result[field].iloc[0]), f"{field} still NaN"


class TestImputeAllMissing:
    def test_all_features_missing_are_filled(self, fitted_imputer):
        row = {f: np.nan for f in NUMERIC_HOME_FEATURES}
        df = pd.DataFrame([row])
        result = fitted_imputer.impute(df)
        for field in NUMERIC_HOME_FEATURES:
            assert not np.isnan(result[field].iloc[0]), f"{field} still NaN"

    def test_all_missing_values_within_training_range(self, fitted_imputer, training_stats):
        row = {f: np.nan for f in NUMERIC_HOME_FEATURES}
        df = pd.DataFrame([row])
        result = fitted_imputer.impute(df)
        for field in NUMERIC_HOME_FEATURES:
            val = result[field].iloc[0]
            stats = training_stats[field]
            assert stats["min"] <= val <= stats["max"], (
                f"{field}={val} outside [{stats['min']}, {stats['max']}]"
            )


class TestImputePreservesNonFeatureColumns:
    def test_extra_columns_untouched(self, fitted_imputer, complete_row):
        row = {**complete_row, "zipcode": "98042", "extra_col": "hello"}
        df = pd.DataFrame([row])
        result = fitted_imputer.impute(df)
        assert result["zipcode"].iloc[0] == "98042"
        assert result["extra_col"].iloc[0] == "hello"


class TestImputerDeterminism:
    def test_same_input_same_output(self, fitted_imputer, complete_row):
        row = {**complete_row, "bathrooms": np.nan}
        df1 = pd.DataFrame([row])
        df2 = pd.DataFrame([row])
        r1 = fitted_imputer.impute(df1)
        r2 = fitted_imputer.impute(df2)
        pd.testing.assert_frame_equal(r1, r2)
