# -*- coding: utf-8 -*-
"""
Created on Sun Feb 13 11:34:07 2022

@author: Markus Brandt
"""

import numpy as np
import pandas as pd

df = pd.DataFrame({'GP Joule Standard': {'Umgebungstemperaturkennlinie': [-10,0,10,15,30],
                                          'Vorlauftemperaturkennlinie': [78, 75, 72, 70, 70],
                                          'Rücklauftemperatur': [50, 50, 50, 50, 50, 50]},
                    'Heißwassernetz': {'Umgebungstemperaturkennlinie': [-20,-10,0,10,20,30],
                                      'Vorlauftemperaturkennlinie': [120, 120, 105, 85, 80, 80],
                                      'Rücklauftemperatur': [50, 50, 50, 50, 50, 50]},
                    'Niedertemperaturnetz': {'Umgebungstemperaturkennlinie': [-20,-10,0,10,20,30],
                                            'Vorlauftemperaturkennlinie': [55, 55, 53, 46, 40, 41],
                                            'Rücklauftemperatur': [30, 30, 30, 30, 30, 30]}
                    })

df.to_json("Daten/Vorlauftemperaturdaten")