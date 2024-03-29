# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 15:29:36 2022

@author: Markus Brandt
"""

from io import BytesIO
import pandas as pd
import numpy as np

import datetime

import demandlib.bdew as bdew
import demandlib.particular_profiles as profiles

import requests
import json

import streamlit as st

from geopy.geocoders import Nominatim

import folium
from folium.features import LatLngPopup



# %% Funktionen

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')


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
                   dataset='merra2', capacity=1.0, height=10,
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


def irradiance_global(irradiance_direct, irradiance_diffuse, tilt, albedo=0.2):
    '''
    parameter
    ---------
    irradiance_direct : numeric
        direct radiation on a tilted area in kW/m²
    irradiance_diffuse : numeric
        diffuse radiation on a tilted area in kW/m²
    tilt : numeric
        How far the panel is inclined from the horizontal, in degrees. 
        A tilt of 0° is a panel facing directly upwards, 
        90° is a panel installed vertically, facing sideways.
    albedo : numeric
        Albedo is the measure of the diffuse reflection of solar radiation
        
    returns
    -------
    total irradiaten : numeric
        total irradiation (sum of diffuse, direct and reflection)
    '''
    irradiance_refl = np.array(irradiance_diffuse) * albedo * (1 - np.cos(tilt)) / 2
    irradiation = np.array(irradiance_direct) + np.array(irradiance_diffuse) + np.array(irradiance_refl)
    return irradiation


@st.cache
def pv_power(irradiance_direct, irradiance_diffuse, eta_pv=0.17,
             albedo=0.2, tilt=35, eta_wr=0.98, system_loss=0.17):
    '''
    parameter
    ---------
    albedo : numeric 
        Albedo is the measure of the diffuse reflection of solar radiation 
        from 0, corresponding to a black body that absorbs all incident radiation, 
        to 1, corresponding to a body that reflects all incident radiation. 
    irradiation_direct : numeric
        direct radiation on a tilted area in kW/m²
    irradiation_diffuse : numeric
        diffuse radiation on a tilted area in kW/m²
    tilt : numeric
        How far the panel is inclined from the horizontal, in degrees. 
        A tilt of 0° is a panel facing directly upwards, 
        90° is a panel installed vertically, facing sideways.
    eta_wr : numeric
        inverter efficiency
    eta_pv : numeric
        photovoltaic efficiency
    returns
    -------
    pv_output : numeric
        PV power output in kW/m²
    '''
    return irradiance_global(irradiance_direct, irradiance_diffuse, tilt) * (1-system_loss) * eta_pv * eta_wr


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
def st_power(umgebungstemperatur, vorlauftemperatur, ruecklauftemperatur,
             irradiance_direct, irradiance_diffuse, tilt,
             eta_k0=0.73, a1=1.7, a2=0.016):
    np.seterr(divide='ignore', invalid='ignore')
    E_global = irradiance_global(irradiance_direct, irradiance_diffuse, tilt)
    T_kol = (np.array(vorlauftemperatur) + np.array(ruecklauftemperatur)) / 2
    eta_k = eta_k0 - a1 * (np.array(T_kol) - np.array(umgebungstemperatur)) / (E_global*1000) \
                    - a2 * (np.array(T_kol) - np.array(umgebungstemperatur))**2 / (E_global*1000)
    eta_k[eta_k < 0] = 0
    return E_global * eta_k


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

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '#,##0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def bdew_heat_demand(year, building_class, ann_demands_per_type, holidays, temperature):
    demand = pd.DataFrame(
        index=pd.date_range(
            datetime.datetime(year, 1, 1, 0), periods=len(temperature), freq="H"
        )
    )
    
    for entry in ann_demands_per_type:
        if entry == "efh" or entry == "mfh":
            demand[entry.upper()] = bdew.HeatBuilding(
                demand.index,
                holidays=holidays,
                temperature=temperature,
                shlp_type=entry,
                building_class=building_class,
                wind_class=1,
                annual_heat_demand=ann_demands_per_type[entry],
               name=entry,
            ).get_bdew_profile()
        else:
            demand[entry.upper()] = bdew.HeatBuilding(
                demand.index,
                holidays=holidays,
                temperature=temperature,
                shlp_type=entry,
                wind_class=1,
                annual_heat_demand=ann_demands_per_type[entry],
                name=entry,
            ).get_bdew_profile()
    return demand


def bdew_electricity_demand(year, ann_el_demand_per_sector, holidays):
    e_slp = bdew.ElecSlp(year, holidays=holidays)
    demand = e_slp.get_profile(ann_el_demand_per_sector).resample("H").mean()
    return demand


def find_location(city, country):                                               # same function as location_coordinates but without streamlit cache -> to hide operation in app
    geolocator = Nominatim(user_agent="my_user_agent")
    coordinates = geolocator.geocode(city+','+ country)
    return coordinates
