import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH CARNEVALL 600", layout="centered")

# --- DATABASE CONNECTION ---
try:
    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("🚨 SPREADSHEET URL PUUTTUU SECRETSISTÄ!")
    st.stop()

def get_data():
    # Käytetään uutta välilehden nimeä 'Logi'
    return conn.read(spreadsheet=spreadsheet_url, worksheet="Logi", ttl=0)

# ... [Kirjautumislogiikka pidetään samana] ...

# --- DATA LOAD ---
try:
    df_logs = get_data()
    # Käytetään uusia sarakkeita: Pvm, Nostaja, Paino, Toistot
    df_logs['Paino'] = pd.to_numeric(df_logs['Paino'], errors='coerce')
    df_logs['Toistot'] = pd.to_numeric(df_logs['Toistot'], errors='coerce')
    df_logs['1RM'] = df_logs['Paino'] * (1 + df_logs['Toistot'] / 30.0)
    
    lifter_maxes = df_logs.groupby('Nostaja')['1RM'].max().to_dict()
    for name in st.secrets["users"].keys():
        if name not in lifter_maxes: lifter_maxes[name] = 0.0
    current_total = sum(lifter_maxes.values())
except Exception as e:
    st.error(f"⚠️ Sheets-virhe: {e}")
    lifter_maxes = {name: 0.0 for name in st.secrets["users"].keys()}
    current_total = 0.0
    df_logs = pd.DataFrame(columns=["Pvm", "Nostaja", "Paino", "Toistot"])

# ... [Tilannehuoneen UI pidetään samana] ...

# --- NOSTO (Tallennus uusilla nimillä) ---
with tab3:
    st.subheader("MERKKAA UUSI NOSTO")
    current_user = st.session_state.get('user', 'Tuntematon')
    
    with st.form("lift_form", clear_on_submit=True):
        w = st.number_input("Paino (kg)", step=2.5, min_value=0.0)
        r = st.number_input("Toistot", step=1, min_value=1)
        submit = st.form_submit_button("TALLENNA NOSTO")
        
        if submit:
            new_row = pd.DataFrame([{
                "Pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Nostaja": current_user,
                "Paino": float(w),
                "Toistot": int(r)
            }])
            updated_df = pd.concat([df_logs, new_row], ignore_index=True)
            # Tallennetaan välilehdelle 'Logi'
            conn.update(spreadsheet=spreadsheet_url, worksheet="Logi", data=updated_df)
            st.success("Tallennettu! Päivitä sivu (F5).")
            st.rerun()
