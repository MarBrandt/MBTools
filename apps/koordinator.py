"""App zur Bestimmung von Wetterdaten und regenerativen Energien.
"""

import pandas as pd
import plotly.express as px
import numpy as np
import datetime
import matplotlib.pyplot as plt

import streamlit as st

import apps.functions as functions


# %% App
def app():
    st.markdown("<h1 style='text-align: center; color: red;'>Der Koordinater</h1>", unsafe_allow_html=True)
    
    st.markdown("<center>Dir liegen Gebäude mit Adresse und Wärmebedarf vor und du stehst nun vor der Aufgabe diese Daten in dein QGIS einzupflegen?!</center>", unsafe_allow_html=True)
    st.markdown("<center>Dummerweise hat man vergessen den Längen- und Breitengrad anzugeben ... und du musst jetzt alles per Hand eintragen?!</center>", unsafe_allow_html=True)
    st.markdown("<center></center>", unsafe_allow_html=True)
    st.markdown("<center></center>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center; color: red;'>Schritt 1: Gib die betreffende Gemeinde ein:</h3>", unsafe_allow_html=True)
    

# %% Ort festlegen
    with st.container():
        filler_col1, disp_col, filler_col2 = st.columns([1, 2, 1])

        # Linke Seite
        country = "Germany"
        
        st.session_state["city"] = disp_col.text_input('Stadt:',)
        st.session_state["Ortschaft"] = functions.location_coordinates(st.session_state["city"], country)
        
        #  Rechte Spalte
        m = functions.create_map(city=st.session_state["city"],
                                  latitude=st.session_state["Ortschaft"].latitude,
                                  longitude=st.session_state["Ortschaft"].longitude)
        disp_col.write(m)
        
        
# %% Einlesen der Adressen
    with st.container():
        st.write("")
        st.markdown("<h3 style='text-align: center; color: red;'>Schritt 2: Lade eine Liste mit den Straßennamen und Hausnummern hoch:</h3>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Lade Excel-Datei hoch!")
        
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)
            
        
        # %% Auswählen der entsprechenden Spalten
            st.markdown("<h3 style='text-align: center; color: red;'>Schritt 3: Wähle bei welcher Spalte es sich um die Straße bzw. Hausnummer handelt:</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            street_column = col1.selectbox("Straßen: ", options=df.columns)
            streets = df[street_column].astype(str)
            hnr_column = col2.selectbox("Hausnummern: ", options=df.columns)
            hnr = df[hnr_column].astype(str)
        
            df["latitude"] = np.nan       # latitude
            df["longitude"] = np.nan      # longitude
            
            st.markdown("<h3 style='text-align: center; color: red;'>Schritt 4: Starten der Koordinatenermittlung:</h3>", unsafe_allow_html=True)
            
            a, b, c, d, e = st.columns(5)
            start_koordinaten_ermittlung = c.button('Koordinatenermittlung starten!')
            if start_koordinaten_ermittlung:
                progress_bar = st.progress(0)
                
                i = 0   # Zählt die Anzahl der Durchläufe in der for-loop
                n = 0   # Zählt die Anzahl nicht gefundener Adressen
                for index, row in df.iterrows():
                    progress_bar.progress(0 + i/len(hnr))
                    try:
                        coordinates = functions.find_location("{}, {} {}".format(st.session_state["city"], row[street_column], row[hnr_column]), country)
                        df["longitude"][i] = coordinates.longitude
                        df["latitude"][i] = coordinates.latitude
                        i += 1
                        
                    except:
                        df["longitude"][i] = np.nan
                        df["latitude"][i] = np.nan
                        n += 1
                        i += 1
                
                result = functions.to_excel(df)
                if n > 0:
                    st.write("Insgesamt konnten {} Adressen nicht gefunden werden. Im Ausgabedatensatz werden bei diesen Adressen keine Koordinaten angegeben. Füge Sie per Hand ein oder prüfe deine Eingaben".format(n))
                
                d1, d2, d3, d4, d5 = st.columns(5)
                d3.download_button(label='📥 Download Koordinaten',
                                    data=result,
                                    file_name='Koordinatorergebnisse_{}.xlsx'.format(st.session_state["city"]))