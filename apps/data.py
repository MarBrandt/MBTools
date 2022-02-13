# -*- coding: utf-8 -*-
"""
Created on Sun Feb 13 11:34:07 2022

@author: Markus Brandt
"""

import numpy as np
import pandas as pd

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

t=[-20,-10,0,10,20,30]

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





test = vorlauftemperatur(x=data["Heißwassernetz"]["Umgebungstemperaturkennlinie"],
                         y=data["Heißwassernetz"]["Vorlauftemperaturkennlinie"],
                         umgebungstemperatur=t)