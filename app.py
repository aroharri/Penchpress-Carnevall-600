# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2 DIAGNOSTICS")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE FIX: MANUAL ID ACCESS ---
SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
# Rakennetaan puhdas URL koodin sisällä
CLEAN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

st.write("### 🔍 Yritetään yhteyttä puhdistetulla ID:llä...")

def load_data_v3():
    # Kokeillaan ladata välilehdet pakotetulla URL:lla
    u = conn.read(spreadsheet=CLEAN_URL, worksheet="users", ttl=0)
    l = conn.read(spreadsheet=CLEAN_URL, worksheet="logi", ttl=0)
    s = conn.read(spreadsheet=CLEAN_URL, worksheet="settings", ttl=0)
    return u, l, s

try:
    df_u, df_l, df_s = load_data_v3()
    st.success("✅ YHTEYS ONNISTUI!")
    st.write("**Löytyneet käyttäjät:**")
    st.dataframe(df_u.head())
    
    st.info("Nyt kun yhteys toimii, voit palauttaa varsinaisen äpin koodin ja käyttää tätä SHEET_ID -tapaa sielläkin.")
    
except Exception as e:
    st.error(f"❌ Yhteys epäonnistui edelleen.")
    st.code(f"Virhe: {e}")
    
    st.markdown("""
    **Jos virhe on edelleen 400 Bad Request, tarkista nämä Sheetsistä:**
    1. Paina **Share** -> Varmista että on **'Anyone with the link'** ja **'Editor'**.
    2. Varmista ettei välilehtien nimissä ole välilyöntejä (esim. 'users ' vs 'users').
    3. Olethan poistanut kaikki 'ä' ja 'ö' kirjaimet välilehtien nimistä?
    """)
