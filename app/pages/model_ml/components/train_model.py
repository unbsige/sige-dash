import xgboost as xgb
import plotly.graph_objects as go
import pandas as pd
import lightgbm as lgb
import streamlit as st
from pages.model_ml.components.physical_model import PhysicalModel
from metric_utils import calculate_forecast_accuracy
from config.settings import IRRADIATION_FEATURES


def train_evaluate_model(model_type, datasets, target):
    df_train = datasets["df_train"]
    df_test = datasets["df_test"]

    if model_type == "XGBoost":
        df_pred = train_xgboost(df_train, df_test, target)
    elif model_type == "LightGBM":
        df_pred = train_lightgbm(df_train, df_test, target)
    elif model_type == "Physical":
        df_pred = train_physical_model(df_train, df_test, target)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    return df_pred


def train_xgboost(df_train, df_test, target):
    with st.spinner("Treinando o modelo XGBoost..."):

        x_train = df_train.drop(columns=[target])
        y_train = df_train[target]
        x_test = df_test.drop(columns=[target])
        y_test = df_test[target]

        model = xgb.XGBRegressor()
        model.fit(
            x_train,
            y_train,
            eval_set=[(x_train, y_train), (x_test, y_test)],
        )

    st.success("Modelo XGBoost treinado com sucesso!")
    plot_feature_importance(model)

    y_pred = model.predict(x_test)
    y_pred = pd.DataFrame(y_pred, index=df_test.index, columns=["y_pred"])
    y_pred["y_true"] = df_test[target]
    metrics = calculate_forecast_accuracy(y_pred["y_true"], y_pred["y_pred"], df_train[target])

    st.write("XGBoost treinado com sucesso!")
    return y_pred, metrics


def train_lightgbm(df_train, df_test, target):
    with st.spinner("Treinando o modelo LightGBM..."):

        x_train = df_train.drop(columns=[target])
        y_train = df_train[target]
        x_test = df_test.drop(columns=[target])
        y_test = df_test[target]

        model = lgb.LGBMRegressor()
        model.fit(
            x_train,
            y_train,
            eval_set=[(x_train, y_train), (x_test, y_test)],
        )

    st.success("Modelo LightGBM treinado com sucesso!")
    plot_feature_importance(model)

    y_pred = model.predict(x_test)
    y_pred = pd.DataFrame(y_pred, index=df_test.index, columns=["y_pred"])
    y_pred["y_true"] = df_test[target]
    metrics = calculate_forecast_accuracy(y_pred["y_true"], y_pred["y_pred"], df_train[target])

    st.write("LightGBM treinado com sucesso!")
    return y_pred, metrics


def train_physical_model(df_train, df_test, target):
    with st.spinner("Treinando o modelo físico..."):
        exclude_features = df_train.columns.difference(IRRADIATION_FEATURES)

        columns = df_train.columns
        model_type = "NL"
        errors = []

        if "air_temp" not in columns:
            errors.append("O modelo físico requer recurso: 'air_temp'")
        if "ghi" not in columns and "gti" not in columns:
            errors.append("O modelo físico requer recurso:'ghi' ou 'gti'")

        if errors:
            error_message = "Erro(s) ao treinar o modelo físico:\n" + "\n".join(f"- {error}" for error in errors)
            st.error(error_message)
            return None

        if "ghi" in columns and "gti" in columns:
            df_train = df_train.drop(columns=["gti"])
            df_test = df_test.drop(columns=["gti"])
            st.info("As colunas 'ghi' e 'gti' estavam presentes. A coluna 'gti' foi removida para evitar redundância.")

        model = PhysicalModel(model_type)
        X_train = df_train.drop(columns=exclude_features).values.T
        y_train = df_train[target].values
        model.fit(X_train, y_train)
        st.success("Modelo físico treinado com sucesso!")

        X_eval = df_test.drop(columns=exclude_features).values
        X_eval_t = X_eval.T

        y_pred = model.predict(X_eval_t)
        y_pred = pd.DataFrame(y_pred, index=df_test.index, columns=["y_pred"])
        y_pred["y_true"] = df_test[target]

        st.write("Modelo físico treinado com sucesso!")
        metrics = calculate_forecast_accuracy(y_pred["y_true"], y_pred["y_pred"], df_train[target])
        return y_pred, metrics


def plot_feature_importance(model, lower_bound=0.1):
    model_name = model.__class__.__name__

    feature_importance = get_feature_importance(model)
    feature_importance = feature_importance[feature_importance['percentage'] > lower_bound]
    plot_data = feature_importance.sort_values('percentage', ascending=True)
    
    with st.expander("Importância dos Recursos ", expanded=True):
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=plot_data['feature'],
            x=plot_data['percentage'],
            orientation='h',
            marker=dict(
                color=plot_data['percentage'],
                colorscale='Viridis',
                line=dict(color='rgba(255, 255, 255, 0.5)', width=0.5)
            ),
            opacity=0.8
        ))

        fig.update_layout(
            title=f"Importância dos Recursos ({model_name})",
            xaxis_title="Importância (%)",
            yaxis_title="Variável",
            font=dict(family="Arial", size=14, color="white"),
            title_font_size=24,
            xaxis_title_font_size=16,
            yaxis_title_font_size=16,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                gridwidth=0.5,
                color="white"
            ),
            yaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                gridwidth=0.5,
                color="white"
            ),
            margin=dict(l=20, r=20, t=60, b=20),
            height=max(350, len(plot_data) * 30)  # Ajuste dinâmico da altura
        )

        for i, value in enumerate(plot_data['percentage']):
            fig.add_annotation(
                x=value,
                y=i,
                text=f"{value:.1f}%",
                showarrow=False,
                xanchor='left',
                xshift=10,
                font=dict(size=12, color="white")
            )

        st.plotly_chart(fig, use_container_width=True)


def get_feature_importance(model):
    if isinstance(model, xgb.XGBRegressor):
        importance = model.feature_importances_
        feature_names = model.feature_names_in_
    elif isinstance(model, lgb.LGBMRegressor):
        importance = model.feature_importances_
        feature_names = model.feature_name_
    else:
        raise ValueError("Modelo não suportado. Use XGBoost ou LightGBM.")

    features_importance = pd.DataFrame({
        "feature": feature_names,
        "importance": importance
    })

    total_importance = features_importance["importance"].sum()
    features_importance["percentage"] = (features_importance["importance"] / total_importance) * 100

    return features_importance.sort_values("percentage", ascending=False)
