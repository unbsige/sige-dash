import json
from pathlib import Path

import pandas as pd

from src.config.settings import ML_CONFIG, PLANTS_CONFIG


class PVDataProcessor:
    def __init__(self, plant_key):
        self.plant_config = PLANTS_CONFIG.get(plant_key)
        self.data_path = Path(ML_CONFIG["DATA_PATH"])
        self.data_file = Path(self.plant_config["data_source"]["file"])
        self.feature_catalog = self._load_feature_catalog()
        self.target_col = ML_CONFIG["TARGET_COL"]
        self.train_start = ML_CONFIG["DATE_SPLIT"]["train_start"]
        self.train_end = ML_CONFIG["DATE_SPLIT"]["train_end"]
        self.test_start = ML_CONFIG["DATE_SPLIT"]["test_start"]
        self.test_end = ML_CONFIG["DATE_SPLIT"]["test_end"]
        self.raw_data = None
        self.processed_data = None

    def load_raw_data(self):
        """Load raw CSV data for a plant."""
        csv_path = self.data_path / "raw" / f"{self.data_file}"

        if not csv_path.exists():
            raise FileNotFoundError(f"Data file not found: {csv_path}")

        df = pd.read_csv(csv_path, parse_dates=["date_time"], index_col="date_time")
        df = df.sort_index()

        self.raw_data = df
        return df

    def generate_all_features(self, df=None):
        if df is None:
            df = self.raw_data.copy()

        if df is None:
            raise ValueError("No data loaded. Call load_raw_data first.")

        df_features = df.copy()

        return df_features

    def get_available_features(self):
        if self.processed_data is None:
            return []

        all_features = list(self.processed_data.columns)
        return [col for col in all_features if col != "ac_power_measured"]

    def get_feature_info(self, feature_name: str):
        for category, features in self.feature_catalog.items():
            if feature_name in features:
                return features[feature_name]

        return {
            "description": feature_name.replace("_", " ").title(),
            "unit": "unknown",
            "required": False,
            "category": "other",
        }

    def split_data(self, selected_features, train_start=None, train_end=None, test_start=None, test_end=None):
        if train_start is None:
            train_start = self.train_start
        if train_end is None:
            train_end = self.train_end
        if test_start is None:
            test_start = self.test_start
        if test_end is None:
            test_end = self.test_end

        if self.processed_data is None:
            raise ValueError("No processed data available")

        df = self.processed_data.copy()
        missing_features = [f for f in selected_features if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")

        train_mask = (df.index >= train_start) & (df.index <= train_end)
        test_mask = (df.index >= test_start) & (df.index <= test_end)

        x_train = df.loc[train_mask, selected_features]
        y_train = df.loc[train_mask, self.target_col]
        x_test = df.loc[test_mask, selected_features]
        y_test = df.loc[test_mask, self.target_col]

        return x_train, x_test, y_train, y_test, df.loc[test_mask].index

    def get_feature_importance(self, model, selected_features: list[str]) -> pd.Series:
        if not hasattr(model, "feature_importances_"):
            raise ValueError("Model does not have feature_importances_ attribute")

        importances = model.feature_importances_
        return pd.Series(importances, index=selected_features).sort_values(ascending=False)

    # def _load_feature_catalog(self):
    #     catalog_path = self.config_path / "feature_catalog.json"
    #     with open(catalog_path) as f:
    #         return json.load(f)
