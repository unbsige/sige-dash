import warnings

import streamlit as st

from src.models.physical.pv_model import PVBaselineModel

warnings.filterwarnings("ignore")


def run_pv_simulation(df_data, params, apply_dc_losses=True, apply_ac_losses=True, use_nbr_efficiency=True):
    """Executa a simulação usando o modelo PV."""

    df_subset = df_data.copy()

    model = PVBaselineModel(
        params=params,
        apply_ac_loss=apply_ac_losses,
        apply_dc_loss=apply_dc_losses,
        use_nbr_eff=use_nbr_efficiency,
    )

    with st.spinner("Executando simulação NBR 16274..."):
        coeffs = (
            {"a0": params.dc_loss_coeffs.a0, "a1": params.dc_loss_coeffs.a1, "a2": params.dc_loss_coeffs.a2}
            if apply_dc_losses
            else None
        )

        results = model.calculate_ac_power(df=df_subset, irrad_col="gti", air_temp_col="air_temp", coeffs=coeffs)

    return results
