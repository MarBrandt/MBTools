"""App zur Bestimmung von Wetterdaten und regenerativen Energien.
"""

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import streamlit as st

import apps.functions as functions


def app():
    # %% Datenimport

    power_curves = pd.DataFrame(pd.read_csv("apps/Daten/wind_power_curves.csv"))
    power_curves["Windgeschwindigkeit in m/s"] = power_curves["speed"]
    power_curves.set_index("Windgeschwindigkeit in m/s", inplace=True)
    power_curves.drop("speed", axis=1, inplace=True)
    
    for entry in power_curves.columns:
        x = entry.split(".")
        y = " ".join(x)
        print(" ".join(x))
        
        power_curves.rename(columns={entry: y}, inplace=True)
        
    
    # %% App
    
    st.markdown("<h1 style='text-align: center; color: red;'>Leistungskurven von Windenergieanlagen</h1>", unsafe_allow_html=True)
    st.markdown("<center>Wähle verschiedene Windkraftanlagen aus und vergleiche die Leistungskurven (Daten von <a href='https://www.renewables.ninja/' target='_blank'>renewables.ninja</a>)</center>", unsafe_allow_html=True)


# %% Auswahl der Anlagen, die miteinander verglichen werden sollen

    st.session_state["wka1"] = st.selectbox("Windkraftanlage 1", options=list(power_curves.columns), index=30)
    st.session_state["wka2"] = st.selectbox("Windkraftanlage 2", options=list(power_curves.columns), index=70)
    st.session_state["wka3"] = st.selectbox("Windkraftanlage 3", options=list(power_curves.columns), index=42)
        
    col1, col2, col3, col4, col5 = st.columns(5)
    col3.download_button(label="Datensatz herunterladen!",
                         data=functions.convert_df(power_curves),
                         file_name='Leistungskurven_Windkraft.csv',
                         mime='text/csv',
                         )
    
    y1 = power_curves[st.session_state["wka1"]]
    y2 = power_curves[st.session_state["wka2"]]
    y3 = power_curves[st.session_state["wka3"]]
    
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(y1, label=st.session_state["wka1"], color='#555759')
    ax.plot(y2, label=st.session_state["wka2"], color='#000000')
    ax.plot(y3, label=st.session_state["wka3"], color='#FFE520')
    ax.set_xlabel("Windgeschwindigkeit in m/s")
    ax.set_ylabel("relative Leistung")
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)