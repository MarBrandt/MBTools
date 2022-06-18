# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 10:23:19 2022

@author: Markus Brandt
"""

import PIL  # Paket zum Laden eines png für das favicon
import streamlit as st
page_icon = PIL.Image.open('pictures/GPJoule_Logo.png')
st.set_page_config(page_title='MB Tools',
                   page_icon=page_icon,
                   layout="wide",
                   initial_sidebar_state='expanded',
                   menu_items={
                       'Get Help': 'https://www.gp-joule.de/',
                       'Report a bug': 'https://www.gp-joule.de/',
                       'About': 'https://www.gp-joule.de/'})


from multiapps import MultiApp
from apps import renewables, power_curves, bdew_load_profiles



app = MultiApp()

# %% Hide Menu

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


# %% Sidebar

st.sidebar.image('pictures/gp_logo.jpg')
st.sidebar.markdown("<h2 style='text-align: center; color: red;'>MB Tools</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<center>Hilfsmittel zur Simulation von Energiesystemen</center>", unsafe_allow_html=True)
st.sidebar.markdown("")
st.sidebar.markdown("Wähle aus einer Handvoll Tools, die dir das Arbeiten mit Energiesystemen erleichtern sollen!")
app.add_app('BDEW Standardlastprofile', bdew_load_profiles.app)
app.add_app('Rechner für erneuerbare Energien', renewables.app)
app.add_app('Leistungskurven von WKAs', power_curves.app)
app.run()