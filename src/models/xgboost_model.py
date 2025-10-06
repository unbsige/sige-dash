import xgboost as xgb

from src.models.base_model import BaseMLModel


class XGBoostModel(BaseMLModel):
    """XGBoost model wrapper for the playground."""

    def __init__(self):
        super().__init__("XGBoost", "ml")

    def create_model(self, **params):
        self.model = xgb.XGBRegressor(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.1),
            subsample=params.get("subsample", 1.0),
            colsample_bytree=params.get("colsample_bytree", 1.0),
            random_state=params.get("random_state", 42),
            n_jobs=-1,
            verbosity=0,
        )
        return self.model

    def get_default_params(self):
        return {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "random_state": 42,
        }

    def get_param_ranges(self):
        return {
            "n_estimators": {"min": 50, "max": 500, "step": 50},
            "max_depth": {"min": 3, "max": 15, "step": 1},
            "learning_rate": {"min": 0.01, "max": 0.3, "step": 0.01},
            "subsample": {"min": 0.5, "max": 1.0, "step": 0.1},
            "colsample_bytree": {"min": 0.5, "max": 1.0, "step": 0.1},
        }

    def get_feature_importance(self):
        if not self.is_fitted or not hasattr(self.model, "feature_importances_"):
            return None

        if self.feature_names_:
            importance_dict = dict(zip(self.feature_names_, self.model.feature_importances_))
            return sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)

        return list(enumerate(self.model.feature_importances_))
