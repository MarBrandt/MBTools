"""App zur Bestimmung von Wetterdaten und regenerativen Energien.
"""

import pandas as pd
import plotly.express as px
import numpy as np
import datetime
import matplotlib.pyplot as plt

import streamlit as st

import apps.functions as functions


# %% Datenimport

countries = pd.read_json("apps/Daten/countries")
holidays = {
            datetime.date(2019, 1, 1): "Neujahr",
            datetime.date(2019, 4, 15): "Karfreitag",
            datetime.date(2019, 4, 18): "Ostermontag",
            datetime.date(2019, 5, 1): "Karfreitag",
            datetime.date(2019, 5, 26): "Christi Himmelfahrt",
            datetime.date(2019, 6, 6): "Pfingstmontag",
            datetime.date(2019, 10, 3): "Tag der deutschen Einheit",
            datetime.date(2019, 10, 31): "Reformationstag",
            datetime.date(2019, 12, 25): "1. Weihnachtsfeiertag",
            datetime.date(2019, 12, 26): "2. Weihnachtsfeiertag",
            }


# %% App
def app():
    st.markdown("<h1 style='text-align: center; color: red;'>BDEW Standardlastprofile für Wärme- und Strom</h1>", unsafe_allow_html=True)
    
    st.markdown("<center>Mit dieser App kannst du Lastgänge für Strom- und Wärmebedarfe erstellen</center>", unsafe_allow_html=True)
    st.markdown("<center></center>", unsafe_allow_html=True)


# %% Eingabe Jahr und Standort
    sel_col, disp_col = st.columns(2)

    # Linke Seite
    country = sel_col.selectbox('Land', options=countries.columns)
    st.session_state["city"] = sel_col.text_input('Stadt:',)
    st.session_state["year"] = sel_col.slider('Jahr:', min_value=1980, max_value=2022, value=2004)
          
    st.session_state["Koordinaten"] = functions.location_coordinates(st.session_state["city"], country)
    
    st.session_state["date_time_index"] = pd.date_range(start="{}-01-01".format(st.session_state["year"]),
                                                        end="{}-12-31 23:00".format(st.session_state["year"]),
                                                        freq="H")
    
    sel_col.markdown("<h3 style='text-align: center; color: red;'>Die Koordinaten von {} lauten:</h3>".format(st.session_state["city"]), unsafe_allow_html=True)
    sel_col.markdown("""
                    <ul style='list-style-type:disc'>
                      <li>Breitengrad: {}°</li>
                      <li>Längengrad: {}°</li>
                    </ul>     
                """.format(round(st.session_state["Koordinaten"].latitude,2),
                            round(st.session_state["Koordinaten"].longitude,2)),
                unsafe_allow_html=True)
            
    #  Rechte Spalte
    m = functions.create_map(city=st.session_state["city"],
                              latitude=st.session_state["Koordinaten"].latitude,
                              longitude=st.session_state["Koordinaten"].longitude)
    disp_col.write(m)
    
    st.session_state["date_time_index"] = pd.date_range(start="{}-01-01".format(st.session_state["year"]),
                                                        end="{}-12-31 23:00".format(st.session_state["year"]),
                                                        freq="H")


# %% Eingabe Bedarf

    left, right = st.columns(2)
    with left.expander("Strombedarf in kWh", expanded=False):
        st.session_state["g0"] = st.number_input('G0 - Gewerbe allgemein:', step=500, value=0)
        st.session_state["g1"] = st.number_input('G1 - Gewerbe werktags 8-18 Uhr:', step=500, value=0)
        st.session_state["g2"] = st.number_input('G2 - Gewerbe mit starkem bis überwiegendem Verbrauch in den Abendstunden:', step=500, value=0)
        st.session_state["g3"] = st.number_input('G3 - Gewerbe durchlaufend:', step=500, value=0)
        st.session_state["g4"] = st.number_input('G4 - Laden/Friseur:', step=500, value=0)
        st.session_state["g5"] = st.number_input('G5 - Bäckerei mit Backstube:', step=500, value=0)
        st.session_state["g6"] = st.number_input('G6 - Wochenendbetrieb:', step=500, value=0)
        st.session_state["g7"] = st.number_input('G7 - Mobilfunksendestation:', step=500, value=0)
        st.session_state["l0"] = st.number_input('L0 - Landwirtschaftsbetriebe allgemein:', step=500, value=0)
        st.session_state["l1"] = st.number_input('L1 - Landwirtschaftsbetriebe mit Milchwirtschaft/Nebenerwerbs-Tierzucht:', step=500, value=0)
        st.session_state["l2"] = st.number_input('L2 - Übrige Landwirtschaftsbetriebe:', step=500, value=0)
        st.session_state["h0"] = st.number_input('H0 - Haushalt/Haushalt dynamisiert:', step=500, value=0)
        
        elec_demand_data = {"g0": st.session_state["g0"],
                            "g1": st.session_state["g1"],
                            "g2": st.session_state["g2"],
                            "g3": st.session_state["g3"],
                            "g4": st.session_state["g4"],
                            "g5": st.session_state["g5"],
                            "g6": st.session_state["g6"],
                            "g7": st.session_state["g7"],
                            "l0": st.session_state["l0"],
                            "l1": st.session_state["l1"],
                            "l2": st.session_state["l2"],
                            "h0_dyn": st.session_state["h0"]}
    
    with right.expander("Wärmebedarf in kWh", expanded=False):
        st.session_state["efh"] = st.number_input('EFH: Einfamilienhaus:', step=500, value=0)
        st.session_state["mfh"] = st.number_input('MFH: Mehrfamilienhaus:', step=500, value=0)
        st.session_state["gmk"] = st.number_input('GMK: Metall und Kfz', step=500, value=0)
        st.session_state["gha"] = st.number_input('GHA: Einzel- und Großhandel', step=500, value=0)
        st.session_state["gko"] = st.number_input('GKO: Gebietskörperschaften, Kreditinstitute und Versicherungen', step=500, value=0)
        st.session_state["gbd"] = st.number_input('GBD: sonstige betriebliche Dienstleistung', step=500, value=0)
        st.session_state["gga"] = st.number_input('GGA: Gaststätten', step=500, value=0)
        st.session_state["gbh"] = st.number_input('GBH: Beherbergung', step=500, value=0)
        st.session_state["gwa"] = st.number_input('GWA: Wäschereien, chemische Reinigungen', step=500, value=0)
        st.session_state["ggb"] = st.number_input('GGB: Gartenbau', step=500, value=0)
        st.session_state["gba"] = st.number_input('GBA: Backstube', step=500, value=0)
        st.session_state["gpd"] = st.number_input('GPD: Papier und Druck', step=500, value=0)
        st.session_state["gmf"] = st.number_input('GMF: haushaltsähnliche Gewerbebetriebe', step=500, value=0)
        st.session_state["ghd"] = st.number_input('GHD: Summenlastprofil Gewerbe/Handel/Dienstleistungen', step=500, value=0)
        
        heat_demand_data = {"efh": st.session_state["efh"],
                            "mfh": st.session_state["mfh"],
                            "gmk": st.session_state["gmk"],
                            "gha": st.session_state["gha"],
                            "gko": st.session_state["gko"],
                            "gbd": st.session_state["gbd"],
                            "gga": st.session_state["gga"],
                            "gbh": st.session_state["gbh"],
                            "gwa": st.session_state["gwa"],
                            "ggb": st.session_state["ggb"],
                            "gba": st.session_state["gba"],
                            "gpd": st.session_state["gpd"],
                            "gmf": st.session_state["gmf"],
                            "ghd": st.session_state["ghd"]}
        

    col1, col2, col3 , col4, col5 = st.columns(5)
    start_bdew_calculation = col3.button('BDEW Lastprofile berechnen!')
        
    if start_bdew_calculation:
        st.session_state["Temperaturdaten"] = functions.get_solar_data(lat=st.session_state["Koordinaten"].latitude, lon=st.session_state["Koordinaten"].longitude,
                                                                   date_from='{}-01-01'.format(st.session_state["year"]), date_to='{}-12-31'.format(st.session_state["year"]),
                                                                   dataset='merra2', capacity=1.0, system_loss=0.16, tracking=0,
                                                                   tilt=0, azim=180)
            
        st.session_state["Temperaturdaten"].drop("electricity", axis=1, inplace=True)
        st.session_state["Temperaturdaten"].drop("irradiance_diffuse", axis=1, inplace=True)
        st.session_state["Temperaturdaten"].drop("irradiance_direct", axis=1, inplace=True)
        
        st.session_state["Temperatur"] = st.session_state["Temperaturdaten"]["temperature"]
        
        st.session_state["heat_demand"] = functions.bdew_heat_demand(year=st.session_state["year"], 
                                                                     building_class=4, 
                                                                     ann_demands_per_type=heat_demand_data, 
                                                                     holidays=holidays,
                                                                     temperature=st.session_state["Temperatur"])
        
        st.session_state["elec_demand"] = functions.bdew_electricity_demand(year=st.session_state["year"],
                                                                            holidays=holidays,
                                                                            ann_el_demand_per_sector=elec_demand_data)
        
        df = pd.DataFrame({"Datum": st.session_state["date_time_index"],
                           "Wärmebedarf": st.session_state["heat_demand"].sum(axis=1),
                           "Strombedarf": st.session_state["elec_demand"].sum(axis=1)})
        result = functions.to_excel(df)
        
        d1, d2, d3, d4, d5 = st.columns(5)
        d3.download_button(label='📥 Download BDEW Lastprofile',
                            data=result,
                            file_name= 'BDEW_Lastprofile_{}_{}.xlsx'.format(st.session_state["city"], st.session_state["year"]))
        
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.plot(df["Wärmebedarf"], label="Wärmebedarf", color='#555759')
        ax.plot(df["Strombedarf"], label="Strombedarf", color='#FFE520')
        ax.set_xlabel("Datum")
        ax.set_ylabel("Leistung in kW")
        ax.legend()
        ax.grid(True)
        
        st.pyplot(fig)
