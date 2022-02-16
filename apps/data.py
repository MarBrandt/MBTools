# -*- coding: utf-8 -*-
"""
Created on Sun Feb 13 11:34:07 2022

@author: Markus Brandt
"""

import numpy as np
import pandas as pd

df = pd.DataFrame({'GP Joule Standard': {'Umgebungstemperaturkennlinie': [-20,-10,0,10,20,30],
                                          'Vorlauftemperaturkennlinie': [78, 78, 75, 65, 60, 60],
                                          'Rücklauftemperatur': [50, 50, 50, 50, 50, 50]},
                    'Heißwassernetz': {'Umgebungstemperaturkennlinie': [-20,-10,0,10,20,30],
                                      'Vorlauftemperaturkennlinie': [120, 120, 105, 85, 80, 80],
                                      'Rücklauftemperatur': [50, 50, 50, 50, 50, 50]},
                    'Niedertemperaturnetz': {'Umgebungstemperaturkennlinie': [-20,-10,0,10,20,30],
                                            'Vorlauftemperaturkennlinie': [55, 55, 53, 43, 40, 40],
                                            'Rücklauftemperatur': [30, 30, 30, 30, 30, 30]}
                    })

df.to_json("Daten/Vorlauftemperaturdaten")

data = pd.read_json("Daten/Vorlauftemperaturdaten")

wind = pd.read_json("Daten/Windkraftanlagen")

country = pd.read_excel("Länder.xlsx")
country.to_json("Daten/countries")