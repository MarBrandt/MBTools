"""App zur Bestimmung von Wetterdaten und regenerativen Energien.
"""

import pandas as pd
import plotly.express as px
import numpy as np

import requests
import json

import streamlit as st

from geopy.geocoders import Nominatim

import folium
from folium.features import LatLngPopup

# %% Datenimport

feed_flow_data = pd.read_json("apps/Daten/Vorlauftemperaturdaten")
turbine_model = pd.read_json("apps/Daten/Windkraftanlagen") 


# %% Funktionen
@st.cache(show_spinner=False)
def get_solar_data(lat=51, lon=9, date_from='2019-01-01', date_to='2019-12-31',
                   dataset='merra2', capacity=1.0, system_loss=0.16, tracking=0,
                   tilt=35, azim=180):
    '''
    Parameter:
    ----------
    lat : numeric
        Latitude
    lon : numeric
        Longitude
    date_from : str
        start date in the following form: '2019-01-01'
        date_from and date_to must be in the same 
    date_to : str
        end date in the following form: '2019-12-31'
        date_from and date_to must be in the same year
    dataset : str
        merra2 or sarah: MERRA (1980-2019) has global coverage, while 
        CM-SAF-SARAH (2000-2015) covers only Europe but with higher quality.
    capacity : numeric
        Photovoltaik capacity in kW
    system_loss : numeric
    tracking : numeric
        Tracking of photovoltaic.
            - 0 = no tracking
            - 1 = 1-axis (azimuth)
            - 2 = 2-axis (tilt + azimuth)
    tilt : numeric
        How far the panel is inclined from the horizontal, in degrees. 
        A tilt of 0° is a panel facing directly upwards, 
        90° is a panel installed vertically, facing sideways.
    azim : numeric
        Compass direction the panel is facing (clockwise). 
        An azimuth angle of 180 degrees means poleward facing, so for 
        latitudes >=0 is interpreted as southwards facing, else
        northwards facing.
        
    Returns:
    --------
    electricity : numeric
        kW
    irradiance_diffuse : numeric
        kW/m²
    irradiance_direct : numeric
       kW/m²     
    temperature : numeric 
        °C
    '''
    token = '7300166e11bf11983dfc4d93cd81d6ce4c5bbe41'
    api_base = 'https://www.renewables.ninja/api/'
    
    s = requests.session()
    s.headers = {'Authorization': 'Token ' + token}

    url = api_base + 'data/pv'
    args = {
        'lat': lat,
        'lon': lon,
        'date_from': date_from,
        'date_to': date_to,
        'dataset': dataset,
        'capacity': capacity,
        'system_loss': system_loss,
        'tracking': tracking,
        'tilt': tilt,
        'azim': azim,
        'format': 'json',
        'raw': True
    }
    r = s.get(url, params=args)
    parsed_response = json.loads(r.text)
    data = pd.read_json(json.dumps(parsed_response['data']), orient='index')
    return data

@st.cache(show_spinner=False)
def get_wind_data(lat=51, lon=9, date_from='2019-01-01', date_to='2019-12-31',
                   dataset='merra2', capacity=1.0, height=100,
                   turbine='Enercon E82 2000'):
    '''    
    Parameter:
    ----------
    lat : numeric
        Latitude
    lon : numeric
        Longitude  
    date_from : str
        start date in the following form: '2019-01-01'
        date_from and date_to must be in the same year 
    date_to : str
        end date in the following form: '2019-12-31'
        date_from and date_to must be in the same year
    dataset : str
        merra2 or sarah: MERRA (1980-2019) has global coverage, while 
        CM-SAF-SARAH (2000-2015) covers only Europe but with higher quality.
    capacity : numeric
        Windpower capacity in kW
    height : numeric
        The height of the turbine's tower, that is, how far the blades are
        centred above the ground. Hub heights are limited to
        between 10 and 150 m.
    turbine : str
        The model of wind turbine affects how much power is produced at
        different wind speeds. Model names typically include the manufacturer,
        the blade diameter (in metres) and the rated capacity (in kW or MW).
        See renewables.ninja for all available turbines.
        
    Returns:
    --------
    electricity : numeric
        kW
    wind_speed : numeric
        m/s
    '''
    token = '7300166e11bf11983dfc4d93cd81d6ce4c5bbe41'
    api_base = 'https://www.renewables.ninja/api/'
    
    s = requests.session()
    s.headers = {'Authorization': 'Token ' + token}   
    url = api_base + 'data/wind'

    args = {
        'lat': lat,
        'lon': lon,
        'date_from': date_from,
        'date_to': date_to,
        'capacity': capacity,
        'height': height,
        'turbine': turbine,
        'format': 'json',
        'raw': True
    }
    r = s.get(url, params=args)
    parsed_response = json.loads(r.text)
    data = pd.read_json(json.dumps(parsed_response['data']), orient='index')
    return data

@st.cache
def vorlauftemperatur(x,y,umgebungstemperatur):
    '''
    paramter
    --------
    x : list
        x values to calculate a polyfit of feed flow temperature (Kennlinie Umgebungstemperatur)
    y : list
        y values to calculate polyfit (Kennlinie Vorlauftemperatur)
    umgebungstemperatur : numeric
        ambient temperature
        
    returns
    -------
    feed flow temperature : numeric
        feed flow temperature in dependet on ambient temperature
    '''
    x, y = x, y
    fit = np.polyfit(x,y,3)
    t_u = []
    for t in umgebungstemperatur:
        if t > x[len(x)-1]:
            t_u.append(x[len(x)-1])
        elif t < x[0]:
            t_u.append(x[0])
        else:
            t_u.append(t)
    return np.polyval(fit,t_u)

@st.cache
def location_coordinates(city, country):
    geolocator = Nominatim(user_agent="my_user_agent")
    coordinates = geolocator.geocode(city+','+ country)
    return coordinates

# @st.cache
def create_map(city, longitude, latitude, zoom_start=10):
    m=folium.Map([latitude, longitude], zoom_start=zoom_start)
    m.add_child(LatLngPopup())
    
    folium.Marker(
    location=[latitude, longitude],
    popup=city,
    ).add_to(m)
    return m

def app():
    st.markdown("<h1 style='text-align: center; color: red;'>Rechner für erneuerbare Energien</h1>", unsafe_allow_html=True)
    
    st.markdown("<center>Mit Hilfe dieser App kannst du orts- und jahresbezogene Erträge sowie Randdaten für folgende Anlagen berechnen und die Ergebnisse herunterladen:</center>", unsafe_allow_html=True)
    st.markdown("""
                    <ul style='list-style-type:disc'>
                      <li>Photovoltaik</li>
                      <li>Solarthermie</li>
                      <li>Windkraft</li>
                      <li>Vorlauftemperatur (Wärmenetz)</li>
                    </ul>     
                """, unsafe_allow_html=True)

# %% Umgebungsdaten

    with st.expander("Umgebungsdaten", expanded=False):
        sel_col, disp_col = st.columns(2)

        # Linke Seite
        country = sel_col.selectbox('Land', options=['Deutschland', 'Frankreich', 'Italien', 'USA'])
        city = sel_col.text_input('Stadt:',)
        st.session_state["year"] = sel_col.slider('Jahr:', min_value=1980, max_value=2020, value=2020)
        
        st.session_state["Koordinaten"] = location_coordinates(city, country)
        
        sel_col.markdown("<h3 style='text-align: center; color: red;'>Die Koordinaten von {} lauten:</h3>".format(city), unsafe_allow_html=True)
        sel_col.markdown("""
                        <ul style='list-style-type:disc'>
                          <li>Breitengrad: {}°</li>
                          <li>Längengrad: {}°</li>
                        </ul>     
                    """.format(round(st.session_state["Koordinaten"].latitude,2),
                               round(st.session_state["Koordinaten"].longitude,2)),
                    unsafe_allow_html=True)
        
        #  Rechte Spalte
        m = create_map(city=city, latitude=st.session_state["Koordinaten"].latitude,
                       longitude=st.session_state["Koordinaten"].longitude)
        disp_col.write(m)
        
        # weiter in der Mitte
        st.text("")
        col1, col2, col3 , col4, col5 = st.columns(5)
        start_weather_download = col3.button('Wetterdaten laden!')
        
        if start_weather_download:
            st.session_state["Umgebungstemperatur"] = pd.DataFrame({'Umgebungstemperatur': get_solar_data(lat=st.session_state["Koordinaten"].latitude, lon=st.session_state["Koordinaten"].longitude,
                                                                     date_from='{}-01-01'.format(st.session_state["year"]), date_to='{}-12-31'.format(st.session_state["year"]),
                                                                     dataset='merra2', capacity=1.0, system_loss=0.16, tracking=0,
                                                                     tilt=0, azim=180)['temperature']})
                                
        if "Umgebungstemperatur" in st.session_state:
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
            st.session_state['Vorlauftemperatur'] = pd.DataFrame({"Vorlauftemperatur": vorlauftemperatur(x=feed_flow_data[feed_flow_curve]['Umgebungstemperaturkennlinie'],
                                                                                       y=feed_flow_data[feed_flow_curve]['Vorlauftemperaturkennlinie'],
                                                                                       umgebungstemperatur=st.session_state['Umgebungstemperatur']['Umgebungstemperatur'])})
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
            pv_power = col_1.number_input('Installierte Leistung [kWp]:', step=100, value=1)
        
        
        # rechte Spalte
        col_2.markdown("<h3 style='text-align: center; color: red;'>Solarthermie</h3>", unsafe_allow_html=True)
        st.session_state["sol_thermal_type"] = col_2.selectbox('Kollektortyp:', options=['Flachkollektor', 'Vakuumröhrenkollektor'])
        st.session_state["sol_thermal_area"] = col_2.number_input('Verfügbare Fläche insgesamt:', step=100, value=1)
        st.session_state["sol_thermal_area_usage"] = col_2.slider('Flächennutzungsgrad Solarthermie [%]:', min_value=0, max_value=100, step=10, value=100)/100
        if st.session_state["sol_thermal_type"] == 'Flachkollektor':
            st.session_state["eta_k0"] = 0.773
            st.session_state["a1"] = 2.270
            st.session_state["a2"] = 0.0181
        else:
            st.session_state["eta_k0"] = 0.581
            st.session_state["a1"] = 0.339
            st.session_state["a2"] = 0.009     
        
        # weiter in der mitte
        
        col1, col2, col3 , col4, col5 = st.columns(5)
        start_pv_st_calc = col3.button('PV und Solarthermie berechnen!')
        

# %% Windkraft
    with st.expander("Windkraft", expanded=False):
        st.session_state["wind_type"] = st.selectbox('Turbinentyp:', options=list(turbine_model[0]))
        st.session_state["wind_height"] = st.number_input('Nabenhöhe [m]:', step=5, value=100, min_value=10, max_value=150)
        st.session_state["wind_power"] = st.number_input('Nennleistung [kW]:', step=100, value=2000)
        
        col1, col2, col3 , col4, col5 = st.columns(5)
        start_wind_calc = col3.button('Berechnung Windkraft starten!')
        
        if start_wind_calc:
            st.session_state["wind_data"] = pd.DataFrame({"el. Leistung in kW": get_wind_data(lat=st.session_state["Koordinaten"].latitude,
                                                                                              lon=st.session_state["Koordinaten"].longitude,
                                                                                              date_from='{}-01-01'.format(st.session_state["year"]),
                                                                                              date_to='{}-12-31'.format(st.session_state["year"]),
                                                                                              capacity=st.session_state["wind_power"],
                                                                                              height=st.session_state["wind_height"],
                                                                                              turbine=st.session_state["wind_type"])["electricity"],
                                                          "Windgeschwindigkeit in m/s": get_wind_data(lat=st.session_state["Koordinaten"].latitude,
                                                                                                      lon=st.session_state["Koordinaten"].longitude,
                                                                                                      date_from='{}-01-01'.format(st.session_state["year"]),
                                                                                                      date_to='{}-12-31'.format(st.session_state["year"]),
                                                                                                      capacity=st.session_state["wind_power"],
                                                                                                      height=st.session_state["wind_height"],
                                                                                                      turbine=st.session_state["wind_type"])["wind_speed"]})
        # if "wind_data" in st.session_state:
        #     st.write(st.session_state["wind_data"])
        
        if "wind_data" in st.session_state:
            plotly_fig = px.line(data_frame=st.session_state['wind_data'],
                                  y="el. Leistung in kW",
                                  color_discrete_sequence = ['darkorange']).update_layout(showlegend=False)
            plotly_fig.update_xaxes(visible=False)
            st.plotly_chart(plotly_fig, use_container_width=True)