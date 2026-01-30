import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH CARNEVALL 600", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # Luetaan treeniloki ja lasketaan jokaisen nostajan paras 1RM
    df = conn.read(worksheet="Treeniloki")
    return df

# --- CSS (Pidetään aiempi tyyli) ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; padding: 10px; z-index: 1000; justify-content: center; }
    .lifter-card { background-color: #1a1a1a; padding: 10px; border-radius: 8px; border-left: 5px solid #FF0000; margin-bottom: 10px; }
    h1 { color: #FF0000 !important; font-family: 'Arial Black'; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (Kuten aiemmin st.secrets["users"] avulla) ---
# ... (Kirjautumiskoodi tähän) ...

# --- DATA PROCESSING ---
try:
    df_logs = get_data()
    # Lasketaan 1RM jokaiselle riville: paino * (1 + reps/30)
    df_logs['1RM'] = df_logs['Paino'] * (1 + df_logs['Toistot'] / 30.0)
    
    # Haetaan jokaisen nostajan tuorein/paras maksimi
    lifter_maxes = df_logs.groupby('Nostaja')['1RM'].max().to_dict()
    
    # Jos joku puuttuu, laitetaan nolla
    for name in st.secrets["users"].keys():
        if name not in lifter_maxes: lifter_maxes[name] = 0.0
        
    current_total = sum(lifter_maxes.values())
except:
    st.warning("Dataa ei löytynyt tai Sheets-yhteys uupuu. Näytetään demo-luvut.")
    lifter_maxes = {"Miikka": 0, "Harri": 0, "Riku": 0, "Jere": 0}
    current_total = 0

# --- NAVIGAATIO ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 TILANNEHUONE", "📈 POLKU", "🏋️ NOSTO", "🎯 TEHTÄVÄT", "👤 MINÄ"])

# --- 1. TILANNEHUONE ---
with tab1:
    st.markdown("<h1>TILANNEHUONE</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("NYT", f"{current_total:.1f} kg")
    c2.metric("TAVOITE", "600 kg")
    c3.metric("PUUTTUU", f"{600 - current_total:.1f} kg")

    fig = go.Figure(go.Indicator(mode="gauge+number", value=current_total, gauge={'axis': {'range': [530, 600]}, 'bar': {'color': "red"}}))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⛓️ SQUAD 1RM STATUS")
    cols = st.columns(2)
    for i, (name, val) in enumerate(lifter_maxes.items()):
        cols[i%2].markdown(f'<div class="lifter-card"><small>{name}</small><br><b>{val:.1f} kg</b></div>', unsafe_allow_html=True)

# --- 3. NOSTO (TALLENNUS SHEETSIIIN) ---
with tab3:
    st.subheader("MERKKAA UUSI NOSTO")
    with st.form("lift_form"):
        w = st.number_input("Paino (kg)", step=2.5)
        r = st.number_input("Toistot", step=1, min_value=1)
        submit = st.form_submit_button("TALLENNA NOSTO")
        
        if submit:
            # Luodaan uusi rivi
            new_data = pd.DataFrame([{
                "Päivämäärä": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Nostaja": st.session_state.user,
                "Paino": w,
                "Toistot": r
            }])
            # Päivitetään Sheets
            updated_df = pd.concat([df_logs, new_data], ignore_index=True)
            conn.update(worksheet="Treeniloki", data=updated_df)
            st.success("Tallennettu Sheetsiin! Päivitä sivu nähdäksesi uudet luvut.")
            st.rerun()

# --- MUUT VÄLILEHDET (POLKU, TEHTÄVÄT, MINÄ) ---
# ... (Kuten aiemmin) ...
