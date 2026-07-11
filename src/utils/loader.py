from __future__ import annotations

import json
import pickle

import pandas as pd


def load_model(model_path: str):
    with open(model_path, "rb") as model_file:
        return pickle.load(model_file)


def load_features(features_path: str) -> list[str]:
    with open(features_path, "r") as features_file:
        return json.load(features_file)


def load_demographics(demographics_path: str) -> pd.DataFrame:
    """Load the full demographics CSV into memory, keyed by zipcode string."""
    return pd.read_csv(demographics_path, dtype={"zipcode": str})