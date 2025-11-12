"""App zur Bestimmung von Wetterdaten und regenerativen Energien.
"""

import pandas as pd
import plotly.express as px
import numpy as np

import streamlit as st

import apps.functions as functions


# %% Datenimport

feed_flow_data = pd.read_json("apps/Daten/Vorlauftemperaturdaten")
turbine_model = pd.read_json("apps/Daten/Windkraftanlagen") 
countries = pd.read_json("apps/Daten/countries")

def app():
    st.markdown("<h1 style='text-align: center; color: red;'>Rechner für erneuerbare Energien</h1>", unsafe_allow_html=True)
    
    st.markdown("<center>Mit Hilfe dieser App kannst du orts- und jahresbezogene Erträge sowie Randdaten für folgende Anlagen berechnen und die Ergebnisse herunterladen</center>", unsafe_allow_html=True)
    st.markdown("<center>Für die Verwendung im Kalkulationstool oder TOP-Energy ist das Jahr 2004 voreingestellt</center>", unsafe_allow_html=True)
    st.markdown("""
                    <ul style='list-style-type:disc'>
                      <li>Lade die Wetterdaten für den gewünschten Ort und das entsprechende Jahr herunter</li>
                      <li>Berechne den Ertrag von Photovoltaik, Solarthermie oder Windkraft</li>
                    </ul>     
                """, unsafe_allow_html=True)
                

# %% Umgebungsdaten

    with st.expander("Umgebungsdaten", expanded=False):
        sel_col, disp_col = st.columns(2)

        # Linke Seite
        country = sel_col.selectbox('Land', options=countries.columns)
        st.session_state["city"] = sel_col.text_input('Stadt:',)
        st.session_state["year"] = sel_col.slider('Jahr:', min_value=1980, max_value=2024, value=2004)
              
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
        
        # weiter in der Mitte
        st.text("")
        col1, col2, col3 , col4, col5 = st.columns(5)
        start_weather_download = col3.button('Wetterdaten laden!')
        
        if start_weather_download:
            st.session_state["Wetterdaten"] = functions.get_solar_data(lat=st.session_state["Koordinaten"].latitude, lon=st.session_state["Koordinaten"].longitude,
                                                                       date_from='{}-01-01'.format(st.session_state["year"]), date_to='{}-12-31'.format(st.session_state["year"]),
                                                                       dataset='merra2', capacity=1.0, system_loss=0.16, tracking=0,
                                                                       tilt=0, azim=180)
            st.session_state["Winddaten"] = functions.get_wind_data(lat=st.session_state["Koordinaten"].latitude,
                                                                    lon=st.session_state["Koordinaten"].longitude,
                                                                    date_from='{}-01-01'.format(st.session_state["year"]),
                                                                    date_to='{}-12-31'.format(st.session_state["year"]))
            
            # st.write(st.session_state["Wetterdaten"])
            st.session_state["Wetterdaten"].drop("electricity", axis=1, inplace=True)
            st.session_state["Wetterdaten"]["Datum"] = st.session_state["date_time_index"]
            st.session_state["Wetterdaten"].set_index("Datum")
            st.session_state["Wetterdaten"]["Windgeschwindigkeit in m/s"] = st.session_state["Winddaten"]["wind_speed"]
            st.session_state["Wetterdaten"]["irradiance_diffuse"] = st.session_state["Wetterdaten"]["irradiance_diffuse"]*1000
            st.session_state["Wetterdaten"]["irradiance_direct"] = st.session_state["Wetterdaten"]["irradiance_direct"]*1000
            st.session_state["Wetterdaten"].rename(columns={"irradiance_diffuse": "Diffusstrahlung in W/m²",
                                                            "irradiance_direct": "Direktstrahlung in W/m²",
                                                            "temperature": "Umgebungstemperatur in °C"}, inplace=True)
                        
            st.session_state["Umgebungstemperatur"] = pd.DataFrame({'Umgebungstemperatur': st.session_state["Wetterdaten"]['Umgebungstemperatur in °C']})
            
        if "Umgebungstemperatur" in st.session_state:
            metric1, metric2, metric3, metric4, metric5 = st.columns(5)
            metric2.metric(label="max. Temperatur", value=np.round(np.max(st.session_state["Umgebungstemperatur"]["Umgebungstemperatur"]),decimals=2), delta="°C")
            metric3.metric(label="min. Temperatur", value=np.round(np.min(st.session_state["Umgebungstemperatur"]["Umgebungstemperatur"]),decimals=2), delta="°C")
            metric4.metric(label="∅ Temperatur", value=np.round(np.average(st.session_state["Umgebungstemperatur"]["Umgebungstemperatur"]),decimals=2), delta="°C")

            df_umgebung = functions.to_excel(st.session_state["Wetterdaten"])
            metric3.download_button(label='📥 Download Wetterdaten {}'.format(st.session_state["city"]),
                                    data=df_umgebung,
                                    file_name= 'Umgebungsdaten_{}_{}.xlsx'.format(st.session_state["city"], st.session_state["year"]))
            
            plotly_fig = px.line(data_frame=st.session_state['Umgebungstemperatur'],
                                 y="Umgebungstemperatur",
                                 color_discrete_sequence = ['darkorange']).update_layout(showlegend=False)
            plotly_fig.update_xaxes(visible=False)
            st.plotly_chart(plotly_fig, use_container_width=True)
            

# %% Vorlauftemperatur        
    with st.expander("Vorlauftemperatur", expanded=False):
        st.markdown("<center>Für die Effizienz einer solarthermischen Anlage ist die Vorlauftemperatur (Austrittstemperatur der Kollektoren) entscheidend.</center>", unsafe_allow_html=True)
        
        feed_flow_curve = st.selectbox("Wähle eine Temperaturkennlinie zum Berechnen der Vorlauftemperatur",
                                        options=feed_flow_data.columns)
        
        if "Umgebungstemperatur" in st.session_state:
            st.session_state['Vorlauftemperatur'] = pd.DataFrame({"Vorlauftemperatur": functions.vorlauftemperatur(x=feed_flow_data[feed_flow_curve]['Umgebungstemperaturkennlinie'],
                                                                                       y=feed_flow_data[feed_flow_curve]['Vorlauftemperaturkennlinie'],
                                                                                       umgebungstemperatur=st.session_state['Umgebungstemperatur']['Umgebungstemperatur']),
                                                                  "Datum": st.session_state["date_time_index"]}).set_index("Datum")
            
            metric1, metric2, metric3, metric4, metric5 = st.columns(5)
            metric2.metric(label="max. Temperatur", value=np.round(np.max(st.session_state["Vorlauftemperatur"]["Vorlauftemperatur"]),decimals=2), delta="°C")
            metric3.metric(label="min. Temperatur", value=np.round(np.min(st.session_state["Vorlauftemperatur"]["Vorlauftemperatur"]),decimals=2), delta="°C")
            metric4.metric(label="∅ Temperatur", value=np.round(np.average(st.session_state["Vorlauftemperatur"]["Vorlauftemperatur"]),decimals=2), delta="°C")
            
            df_vorlauf = functions.to_excel(st.session_state["Vorlauftemperatur"])
            metric3.download_button(label='📥 Download Vorlauftemperatur',
                               data=df_vorlauf,
                               file_name= 'Vorlauftemperatur_{}_{}.xlsx'.format(st.session_state["city"], st.session_state["year"]))
            
            plotly_fig = px.line(data_frame=st.session_state['Vorlauftemperatur'],
                                 y="Vorlauftemperatur",
                                 color_discrete_sequence = ['darkorange']).update_layout(showlegend=False)
            plotly_fig.update_xaxes(visible=False)
            st.plotly_chart(plotly_fig, use_container_width=True)
        elif "Umgebungstemperatur" not in st.session_state:
            st.markdown("<center>Bevor eine jährliche Vorlauftemperatur angezeigt werden kann musst du zunächst die <strong>Wetterdaten laden!</strong></center>",
                        unsafe_allow_html=True)


# %% PV + Solarthermie
    with st.expander("Photovoltaik und Solarthermie", expanded=False):
        st.session_state["Neigung"] = st.slider('Neigungswinkel:', min_value=0, max_value=90, value=25)
        st.session_state["Azimut"] = st.slider('Azimutausrichtung (0°-Norden, 90°-Osten, 180°-Süden, 270°-Westen):',
                                               min_value=0, max_value=359, value=180)
        
        col_1, col_2 = st.columns(2)
        
        # linke Spalte
        col_1.markdown("<h3 style='text-align: center; color: red;'>Photovoltaik</h3>", unsafe_allow_html=True)
        
        st.session_state["pv_type"] = col_1.selectbox('Art der Berechnung:', options=['Berechnung nach Peak-Leistung', 'Berechnung nach Fläche'])
        if st.session_state["pv_type"] == 'Berechnung nach Fläche':
            st.session_state["pv_area"] = col_1.number_input('Verfügbare Fläche [m²]:', step=100, value=1)
            st.session_state["pv_area_usage"] = col_1.slider('Flächennutzungsgrad Photovoltaik [%]:', min_value=0, max_value=100, step=10, value=100)/100
            st.session_state["pv_eta"] = col_1.number_input('Modulwirkungsgrad [%]:', step=1, value=17)/100
        else:
            st.session_state["installed_pv_power"] = col_1.number_input('Installierte Leistung [kWp]:', step=100, value=1)
        
        
        # rechte Spalte
        col_2.markdown("<h3 style='text-align: center; color: red;'>Solarthermie</h3>", unsafe_allow_html=True)
        st.session_state["sol_thermal_type"] = col_2.selectbox('Kollektortyp:', options=['Flachkollektor', 'Vakuumröhrenkollektor'])
        st.session_state["sol_thermal_area"] = col_2.number_input('Verfügbare Fläche insgesamt:', step=100, value=1)
        st.session_state["sol_thermal_area_usage"] = col_2.slider('Flächennutzungsgrad Solarthermie [%]:', min_value=0, max_value=100, step=10, value=100)/100
        if st.session_state["sol_thermal_type"] == 'Flachkollektor':
            st.session_state["eta_k0"] = 0.749
            st.session_state["a1"] = 3.542
            st.session_state["a2"] = 0.042
        else:
            st.session_state["eta_k0"] = 0.687
            st.session_state["a1"] = 0.613
            st.session_state["a2"] = 0.003
            
        st.session_state["ST_Temperaturniveau"] = col_2.selectbox('Temperaturniveau der Einspeisung', options=["Vorlauftemperatur", "festgesetzte Temperatur"])
        
        if st.session_state["ST_Temperaturniveau"] == "festgesetzte Temperatur":
            st.session_state['Austrittstemperatur_Solarthermie'] = col_2.number_input("Austrittstemperatur Solarthermie:", value=60)
            st.session_state['Eintrittstemperatur_Solarthermie'] = col_2.number_input("Eintrittestemperatur Solarthermie:", value=30)
        else:
            if 'Vorlauftemperatur' not in st.session_state:
                print("Lade Temperaturdaten")
            else:
                st.session_state['Austrittstemperatur_Solarthermie'] = st.session_state['Vorlauftemperatur']["Vorlauftemperatur"]
                st.session_state['Eintrittstemperatur_Solarthermie'] = feed_flow_data[feed_flow_curve]['Rücklauftemperatur'][0]
            
                    
                
            
        
        # weiter in der mitte
        
        col1, col2, col3, col4, col5 = st.columns(5)
        start_pv_st_calc = col3.button('PV und Solarthermie berechnen!')
        
        # PV
        if start_pv_st_calc == True:
            pv_st_data = functions.get_solar_data(lat=st.session_state["Koordinaten"].latitude,
                                                  lon=st.session_state["Koordinaten"].longitude,
                                                  date_from='{}-01-01'.format(st.session_state["year"]),
                                                  date_to='{}-12-31'.format(st.session_state["year"]),
                                                  tilt=st.session_state["Neigung"],
                                                  azim=st.session_state["Azimut"])
            
            if st.session_state["pv_type"] == "Berechnung nach Fläche":
                st.session_state["pv_st_output"] = pd.DataFrame({"Photovoltaik": functions.pv_power(irradiance_direct=pv_st_data['irradiance_direct'],
                                                                                                 irradiance_diffuse=pv_st_data['irradiance_diffuse'],
                                                                                                 tilt=st.session_state["Neigung"],
                                                                                                 eta_pv=st.session_state["pv_eta"]) * st.session_state["pv_area"] * st.session_state["pv_area_usage"],
                                                                 "Solarthermie": functions.st_power(irradiance_direct=pv_st_data['irradiance_direct'],
                                                                                             irradiance_diffuse=pv_st_data['irradiance_diffuse'],
                                                                                             tilt=st.session_state["Neigung"],
                                                                                             umgebungstemperatur=st.session_state["Umgebungstemperatur"]["Umgebungstemperatur"],
                                                                                             vorlauftemperatur=st.session_state['Austrittstemperatur_Solarthermie'],
                                                                                             ruecklauftemperatur=st.session_state['Eintrittstemperatur_Solarthermie'],
                                                                                             eta_k0=st.session_state["eta_k0"], 
                                                                                             a1=st.session_state["a1"],
                                                                                             a2=st.session_state["a2"]) * st.session_state["sol_thermal_area"] * st.session_state["sol_thermal_area_usage"]})
            else:
                st.session_state["pv_st_output"] = pd.DataFrame({"Photovoltaik": pv_st_data['electricity'] * st.session_state["installed_pv_power"],
                                                                 "Solarthermie": functions.st_power(irradiance_direct=pv_st_data['irradiance_direct'],
                                                                                             irradiance_diffuse=pv_st_data['irradiance_diffuse'],
                                                                                             tilt=st.session_state["Neigung"],
                                                                                             umgebungstemperatur=st.session_state["Umgebungstemperatur"]["Umgebungstemperatur"],
                                                                                             vorlauftemperatur=st.session_state['Austrittstemperatur_Solarthermie'],
                                                                                             ruecklauftemperatur=st.session_state['Eintrittstemperatur_Solarthermie'],
                                                                                             eta_k0=st.session_state["eta_k0"], 
                                                                                             a1=st.session_state["a1"],
                                                                                             a2=st.session_state["a2"]) * st.session_state["sol_thermal_area"] * st.session_state["sol_thermal_area_usage"]})
            start_pv_st_calc = False
            
        if "pv_st_output" in st.session_state:
            
            metric1, metric2, metric3, metric4, metric5, metric6 = st.columns(6)
            metric1.metric(label="max. Leistung", value=np.round(np.max(st.session_state["pv_st_output"]["Photovoltaik"]),decimals=2), delta="kW")
            metric2.metric(label="Produktion Photovoltaik", value=np.round(np.sum(st.session_state["pv_st_output"]["Photovoltaik"])/1000,decimals=2), delta="MWh")
            metric3.metric(label="Vollbenutzungsstunden", value=np.round(np.sum(st.session_state["pv_st_output"]["Photovoltaik"])/st.session_state["installed_pv_power"],decimals=2), delta="VBH")
            
            metric4.metric(label="max. Leistung", value=np.round(np.max(st.session_state["pv_st_output"]["Solarthermie"]),decimals=2), delta="kW")
            metric5.metric(label="Produktion Solarthermie", value=np.round(np.sum(st.session_state["pv_st_output"]["Solarthermie"])/1000,decimals=2), delta="MWh")
            metric6.metric(label="Vollbenutzungsstunden", value=np.round(np.sum(st.session_state["pv_st_output"]["Solarthermie"])/np.max(st.session_state["pv_st_output"]["Solarthermie"]),decimals=2), delta="VBH")         
            
            df_pv_st = pd.DataFrame({"Datum": st.session_state["date_time_index"],
                                     "Photovoltaik [kW]": st.session_state["pv_st_output"]["Photovoltaik"],
                                     "Solarthermie [kW]": st.session_state["pv_st_output"]["Solarthermie"]}).set_index("Datum")            
            excel_pv_st = functions.to_excel(df_pv_st)
            
            d1, d2, d3, d4, d5 = st.columns(5)
            d3.download_button(label='📥 Download PV/ST-Ertrag',
                               data=excel_pv_st,
                               file_name= 'PV_ST_Ertrag_{}_{}.xlsx'.format(st.session_state["city"], st.session_state["year"]))
            
            plotly_fig = px.line(data_frame=st.session_state["pv_st_output"])
                                 # y="Vorlauftemperatur",
                                 # color_discrete_sequence = ['darkorange']).update_layout(showlegend=False)
            plotly_fig.update_xaxes(visible=False)
            st.plotly_chart(plotly_fig, use_container_width=True)

# %% Windkraft
    with st.expander("Windkraft", expanded=False):
        st.session_state["wind_type"] = st.selectbox('Turbinentyp:', options=list(turbine_model[0]))
        st.session_state["wind_height"] = st.number_input('Nabenhöhe [m]:', step=5, value=100, min_value=10, max_value=300)
        st.session_state["wind_power"] = st.number_input('Nennleistung [kW]:', step=100, value=2000)
        
        col1, col2, col3 , col4, col5 = st.columns(5)
        start_wind_calc = col3.button('Berechnung Windkraft starten!')
        
        if start_wind_calc:
            st.session_state["wind_data"] = pd.DataFrame({"Datum": st.session_state["date_time_index"],
                                                          "el. Leistung in kW": functions.get_wind_data(lat=st.session_state["Koordinaten"].latitude,
                                                                                                        lon=st.session_state["Koordinaten"].longitude,
                                                                                                        date_from='{}-01-01'.format(st.session_state["year"]),
                                                                                                        date_to='{}-12-31'.format(st.session_state["year"]),
                                                                                                        capacity=st.session_state["wind_power"],
                                                                                                        height=st.session_state["wind_height"],
                                                                                                        turbine=st.session_state["wind_type"])["electricity"],
                                                          "Windgeschwindigkeit in m/s": functions.get_wind_data(lat=st.session_state["Koordinaten"].latitude,
                                                                                                                lon=st.session_state["Koordinaten"].longitude,
                                                                                                                date_from='{}-01-01'.format(st.session_state["year"]),
                                                                                                                date_to='{}-12-31'.format(st.session_state["year"]),
                                                                                                                capacity=st.session_state["wind_power"],
                                                                                                                height=st.session_state["wind_height"],
                                                                                                                turbine=st.session_state["wind_type"])["wind_speed"]})
        
        if "wind_data" in st.session_state:
            
            metric1, metric2, metric3, metric4, metric5 = st.columns(5)
            metric2.metric(label="max. Leistung", value=np.round(np.max(st.session_state["wind_data"]["el. Leistung in kW"]),decimals=2), delta="kW")
            metric3.metric(label="Produktion Windenergie", value=np.round(np.sum(st.session_state["wind_data"]["el. Leistung in kW"])/1000,decimals=2), delta="MWh")
            metric4.metric(label="Vollbenutzungsstunden", value=np.round(np.sum(st.session_state["wind_data"]["el. Leistung in kW"])/st.session_state["wind_power"],decimals=2), delta="VBH")
            
            df_wind = functions.to_excel(st.session_state["wind_data"])
            metric3.download_button(label='📥 Download Windkraft',
                               data=df_wind,
                               file_name= 'Ertrag Windkraft_{}_{}.xlsx'.format(st.session_state["city"], st.session_state["year"]))
            
            plotly_fig = px.line(data_frame=st.session_state['wind_data'],
                                  y="el. Leistung in kW",
                                  color_discrete_sequence = ['darkorange']).update_layout(showlegend=False)
            plotly_fig.update_xaxes(visible=False)
            st.plotly_chart(plotly_fig, use_container_width=True)
    
    
    try:
        if "wind_data" and "pv_st_output" and "Umgebungstemperatur" and "Vorlauftemperatur" not in st.session_state:
            st.markdown("<center>Du kannst hier alle Daten gesammelt herunterladen, sobald alle Berechnungen durchgeführt wurden</center>", unsafe_allow_html=True)
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            
            df = pd.DataFrame({"Datum": st.session_state["date_time_index"],
                               "Umgebungstemperatur in °C": st.session_state["Umgebungstemperatur"]["Umgebungstemperatur"],
                               "Windgeschwindigkeit in m/s": st.session_state["wind_data"]["Windgeschwindigkeit in m/s"],
                               "Vorlauftemperatur in °C": st.session_state["Vorlauftemperatur"]["Vorlauftemperatur"],
                               "Photovoltaik in kW": st.session_state["pv_st_output"]["Photovoltaik"],
                               "Solarthermie in kW": st.session_state["pv_st_output"]["Solarthermie"],
                               "Windkraft in kW": st.session_state["wind_data"]["el. Leistung in kW"]})
            
            df_gesamt = functions.to_excel(df)
            c3.download_button(label='📥 Download Wetterdaten',
                               data=df_gesamt,
                               file_name= 'Wetterdaten_{}_{}.xlsx'.format(st.session_state["city"], st.session_state["year"]))
    except:
        st.markdown("<center>Du kannst hier alle Daten gesammelt herunterladen, sobald alle Berechnungen durchgeführt wurden</center>", unsafe_allow_html=True)
            
        
    st.markdown("<center>Diese App benutzt Daten von <a href='https://www.renewables.ninja/' target='_blank'>renewables.ninja</a></center>", unsafe_allow_html=True)
