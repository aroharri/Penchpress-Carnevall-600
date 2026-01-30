# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="FINAL DEBUG")

# Käytetään eri tapaa alustaa yhteys
conn = st.connection("gsheets", type=GSheetsConnection)

# TÄMÄ ON SINUN ID
SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
# Rakennetaan koodiin suora vientilinkki, joka ohittaa kirjaston parsimisen
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

st.write("### 🛠️ Force-Loading Sheets")

def force_load(sheet_name):
    # Luetaan CSV-muodossa suoraan Googlen API:sta, ohittaa monta virhettä
    url = EXPORT_URL + sheet_name
    return pd.read_csv(url)

try:
    df_u = force_load("users")
    st.success("✅ USERS LADATTU!")
    st.dataframe(df_u.head())
    
    df_l = force_load("logi")
    st.success("✅ LOGI LADATTU!")
    
    df_s = force_load("settings")
    st.success("✅ SETTINGS LADATTU!")

    st.balloons()
    st.info("Jos näet datan tässä, voimme rakentaa äpin tällä 'Force-Load' -tavalla, joka on immuuni 400-virheille!")

except Exception as e:
    st.error(f"❌ Force-load epäonnistui: {e}")
    st.markdown("""
    **Jos tämäkin epäonnistuu, tee näin:**
    1. Luo TÄYSIN UUSI Sheets-tiedosto (File -> New).
    2. Kirjoita otsikot KÄSIN (pvm, email, paino...). Älä kopioi vanhasta.
    3. Vaihda uusi ID koodiin.
    """)
