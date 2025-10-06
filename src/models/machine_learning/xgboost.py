import os
import pickle
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb

from src.config.settings import MONTH_MAPPING
from src.config.styles import render_col_divider
from src.data.data_loader import load_historical_data


def create_time_features_minimal(df):
    df_feat = df.copy()
    df_feat["day_of_year"] = df.index.dayofyear
    df_feat["day_of_year_cos"] = np.cos(2 * np.pi * df_feat["day_of_year"] / 365.25)
    df_feat["season"] = (df.index.month % 12) // 3 + 1
    df_feat["day_since"] = (df.index - df.index.min()).days
    return df_feat


def load_xgboost_model():
    model_path = "models/xgboost/xgb_energy_predictor.pkl"

    if not os.path.exists(model_path):
        print(f"Modelo XGBoost não encontrado! Path: {model_path}")
        return None

    try:
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)

        train_mae = model_data.get("train_mae", model_data.get("mae_score", "N/A"))
        print(f"Modelo carregado - Train MAE: {train_mae}")
        return model_data

    except Exception as e:
        print(f"Erro ao carregar modelo: {str(e)}")
        return None


def create_features_for_prediction(df_solar, model_data):
    required_features = model_data["features"]
    df_features = df_solar.copy()

    weather_cols = ["gti_net", "csi_mean", "cell_temp_mean"]
    missing_cols = [col for col in weather_cols if col not in df_features.columns]

    if missing_cols:
        print(f"Colunas meteorológicas ausentes: {missing_cols}")
        return None

    df_features = create_time_features_minimal(df_features)

    try:
        return df_features[required_features]
    except KeyError as e:
        print(f"Features ausentes: {e}")
        return None


def initialize_xgboost_session_state():
    if "xgb_prediction_cache" not in st.session_state:
        st.session_state.xgb_prediction_cache = {}

    if "xgb_selected_period" not in st.session_state:
        current_date = datetime.now()
        st.session_state.xgb_selected_period = {
            "start_date": current_date.date() - timedelta(days=30),
            "end_date": current_date.date(),
        }
