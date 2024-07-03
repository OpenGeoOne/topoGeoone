# LINHAS DE VOO

# https://www.djzphoto.com/blog/2018/12/5/dji-drone-quick-specs-amp-comparison-page
# https://www.dji.com/br/phantom-4-adv/info

import numpy as np

#Dados Air 2S (5472 × 3648)

dc = 13.2e-3  #tamanho do sensor em metros (horizontal - colunas)
dl = 8.8e-3   #tamanho do sensor em metros (vertical - linhas)
f = 8.38e-3   #distância focal (metros)

h = 50 # altura de voo em metros
perc_x = 0.75  # percentual de sobreposição lateral
perc_y = 0.85 # percentual de sobreposição frontal

# Distância linhas de voo paralelas
tg_alfa_2 = (dc/(2*f))
alfa = np.degrees(2*np.arctan(tg_alfa_2))
D = dc*h/f
SD = perc_x*D
h1 = SD/(2*tg_alfa_2)
h2 = h - h1
deltax = h2*SD/h1

# Espaçamento frontal
tg_alfa_2 = (dl/(2*f))
alfa = np.degrees(2*np.arctan(tg_alfa_2))
D = dl*h/f
SD = perc_y*D
h1 = SD/(2*tg_alfa_2)
h2 = h - h1
deltay = h2*SD/h1

print('Sobreposição lateral: ', round(deltax,1))
print('Sobreposição frontal: ', round(deltay,1))