
import pandas as pd

dh_temp = pd.DataFrame(pd.read_excel('Vorlauftemperaturkennlinie.xlsx')).set_index('Temperatur')

x = list(dh_temp)
y = dh_temp.iloc[0].to_list()

print(dh_temp.iloc[1].max())

