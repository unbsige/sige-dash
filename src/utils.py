import pickle
from pathlib import Path


def save_model(model):
    try:
        model_path = Path("modelo/extra_tree_model.joblib")
        with model_path.open(mode="wb") as file:
            pickle.dump(model, file)
    except Exception:
        Path("modelo").mkdir(parents=True, exist_ok=True)
        model_path = Path("modelo/extra_tree_model.joblib")
        with model_path.open(mode="wb") as file:
            pickle.dump(model, file)
