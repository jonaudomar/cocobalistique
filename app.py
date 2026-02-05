import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import time

st.title('cocoBalistique 🥥')

st.text("Cette application calcule la trajectoire d'une noix de coco lancé dans le ciel à partir d'une vitesse initiale et un angle d'inclinaison.")

st.header("Choix des paramètres", divider=True)

# Paramètres
#v0 = 10.0                     # m/s
#alpha = np.deg2rad(45)        # radians
g = 9.81                      # m/s²

v0 = st.slider("Vitesse initiale (m/s) : ", 5, 100, 10)

alpha = st.slider("Angle de tir (degrés)", 5, 85, 45)
alpha = np.deg2rad(alpha)

if st.button("Lancer le programme", type="secondary"):

    st.header("Informations générales", divider=True)

    # Portée
    R = (v0**2 / g) * np.sin(2 * alpha)
    # temps au point d'impact tR à la portée R
    tR = 2*v0*np.sin(alpha)/g

    st.write("La portée du tir est de ", round(R, 2), " mètres. Atteint en ", round(tR, 2), " secondes.")

    #Altitude max H
    H = (v0*np.sin(alpha))**2/(2*g)
    # temps à l'altitude max H
    tH = v0*np.sin(alpha)/g

    st.write("Altitude maximale atteinte ", round(H, 2), " mètres. Atteint en ", round(tH, 2), " secondes.")


    # Axe horizontal x
    x = np.linspace(0, R, 50)

    # Axe horizontal t
    t = np.linspace(0, tR, 50)

    # Trajectoire Y(X)
    y = x * np.tan(alpha) - (g / (2 * v0**2 * np.cos(alpha)**2)) * x**2

    #norme de la vitesse
    v = np.sqrt(v0**2-2*v0*g*t*np.sin(alpha) + (g*t)**2)

    st.header("Graphiques de trajectoire et vitesse", divider=True)

    # Création de la figure
    fig, ax = plt.subplots(2, 1, figsize=(15, 15))

    ax[0].plot(x, y)
    ax[0].set_xlabel("X (m)")
    ax[0].set_ylabel("Y (m)")
    ax[0].set_title("Trajectoire Y(X)")
    ax[0].grid(True)

    ax[1].plot(t, v)
    ax[1].set_xlabel("Temps (s)")
    ax[1].set_ylabel("Vitesse (m/s)")
    ax[1].set_title("Vitesse v(t)")
    ax[1].grid(True)

    st.pyplot(fig)

st.header("Montrez-moi les équations", divider=True)

st.text("Norme de la vitesse (m/s) :")
st.latex(r'''
         v(t) = \sqrt{v_0^2 -2 v_0 gt* \sin\alpha + g^2t^2}
         '''
)

st.text("Hauteur maximale atteinte (m) :")
st.latex(r'''
    H(\alpha) = \frac{v_0^2 \sin^2\alpha}{2g}
    '''
)

st.text("Portée (distance au point d'impact, en m) :")
st.latex(r'''
    R(\alpha) = \frac{v_0^2}{g}\,\sin(2\alpha)
    '''
)

st.text("Temps à la hauteur maximale (s):")
st.latex(r'''
    t_H = \frac{v_0 \sin\alpha}{g}
    '''
)

st.text("Temps au point d'impact (s) :")
st.latex(r'''
    t_R = \frac{2 v_0 \sin\alpha}{g}
    '''
)

if st.button("Merci cocoBalistique"):
    st.balloons()
