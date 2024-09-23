import streamlit as st
from config.settings import INVERTER_MAPPING, PLANT_GROUPS, PLANTS


def get_plant_inverters(plant_name):
    group = PLANT_GROUPS[plant_name]
    return [value for _, value in INVERTER_MAPPING.items() if value["group"] == group]


def select_plant():
    with st.expander("1. Seleção do inversor ou medidor", expanded=True):
        cols = st.columns([0.4, 0.4, 0.2])

        with cols[0]:
            selected_plant = st.selectbox(
                "Selecione a Planta Fotovoltaica",
                options=PLANTS,
                index=None,
                placeholder="Escolha uma planta",
            )

            if not selected_plant:
                # st.warning("🔒 Selecione uma planta fotovoltaica")
                st.stop()

        selected_plant = selected_plant.lower().replace(" ", "_")

        if selected_plant not in ["ldtea", "uac"]:
            # st.warning("🔒 Planta sem dados cadastrados")
            st.stop()

        agg_cols = {
            f"{selected_plant}_total": "Produção Total da Planta",
            f"{selected_plant}_avg": "Média de Todos os Inversores"
        }

        plant_inverters = get_plant_inverters(selected_plant)
        inverter_options = list(agg_cols.values()) + [inv["name"] for inv in plant_inverters]

        with cols[1]:
            selected_target = st.selectbox(
                "Selecione o tipo de medição",
                options=inverter_options,
                index=None,
                placeholder="Escolha o tipo de medição",
            )

            if not selected_target:
                # st.warning("🔒 Por favor, selecione o tipo de medição")
                st.stop()

        if selected_target == agg_cols[f"{selected_plant}_total"]:
            target = f"{selected_plant}_total"
        elif selected_target == agg_cols[f"{selected_plant}_avg"]:
            target = f"{selected_plant}_avg"
        else:
            for inv in plant_inverters:
                if selected_target == inv["name"]:
                    target = inv["col"]
                    break

    if not target:
        st.warning("🔒 Tipo de medição não encontrado")
        st.stop()
    else:
        st.success(f"✅  Planta: {selected_plant.upper()} - Inversor: {selected_target}")
    return target
