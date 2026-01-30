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
    # HUOM: Varmista että Sheetsissäsi on välilehti nimellä 'Treeniloki'
    return conn.read(worksheet="Treeniloki", ttl=0)

# --- CSS ---
st.markdown("<style>.stApp { background-color: #050505; color: #E0E0E0; } .stTabs [data-baseweb='tab-list'] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; padding: 10px; z-index: 1000; justify-content: center; } .main .block-container { padding-bottom: 100px; } .lifter-card { background-color: #1a1a1a; padding: 10px; border-radius: 8px; border-left: 5px solid #FF0000; margin-bottom: 10px; } h1 { color: #FF0000 !important; font-family: 'Arial Black'; text-align: center; text-transform: uppercase; }</style>", unsafe_allow_html=True)

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Ladataan käyttäjät Secretseistä
try:
    USERS = st.secrets["users"]
except:
    st.error("Secrets uupuvat! Lisää [users] Streamlit Cloudin asetuksiin.")
    st.stop()

if not st.session_state.logged_in:
    st.markdown("<h1>⚡ LOGIN</h1>", unsafe_allow_html=True)
    user_choice = st.selectbox("VALITSE NOSTAJA", list(USERS.keys()))
    pin_input = st.text_input("PIN", type="password")
    if st.button("LOGIN"):
        if pin_input == USERS[user_choice]:
            st.session_state.logged_in = True
            st.session_state.user = user_choice
            st.rerun()
        else:
            st.error("Väärä PIN")
    st.stop()

# --- DATA LOAD ---
try:
    df_logs = get_data()
    # Pakotetaan sarakkeet numeerisiksi siltä varalta että Sheetsissä on tekstiä
    df_logs['Paino'] = pd.to_numeric(df_logs['Paino'], errors='coerce')
    df_logs['Toistot'] = pd.to_numeric(df_logs['Toistot'], errors='coerce')
    df_logs['1RM'] = df_logs['Paino'] * (1 + df_logs['Toistot'] / 30.0)
    
    lifter_maxes = df_logs.groupby('Nostaja')['1RM'].max().to_dict()
    for name in USERS.keys():
        if name not in lifter_maxes: lifter_maxes[name] = 0.0
    current_total = sum(lifter_maxes.values())
except Exception as e:
    st.error(f"Sheets-virhe: {e}")
    lifter_maxes = {name: 0.0 for name in USERS.keys()}
    current_total = 0.0
    df_logs = pd.DataFrame(columns=["Päivämäärä", "Nostaja", "Paino", "Toistot"])

# --- UI TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 TILANNEHUONE", "📈 POLKU", "🏋️ NOSTO", "🎯 TEHTÄVÄT", "👤 MINÄ"])

with tab1:
    st.markdown("<h1>TILANNEHUONE</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("NYT", f"{current_total:.1f} kg")
    c2.metric("TAVOITE", "600 kg")
    c3.metric("PUUTTUU", f"{600 - current_total:.1f} kg")
    
    fig = go.Figure(go.Indicator(mode="gauge+number", value=current_total, gauge={'axis': {'range': [530, 600]}, 'bar': {'color': "red"}}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=250)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("MERKKAA UUSI NOSTO")
    # Varmistetaan että user on olemassa ennen formia
    current_user = st.session_state.get('user', 'Tuntematon')
    
    with st.form("lift_form", clear_on_submit=True):
        w = st.number_input("Paino (kg)", step=2.5, min_value=0.0)
        r = st.number_input("Toistot", step=1, min_value=1)
        submit = st.form_submit_button("TALLENNA NOSTO")
        
        if submit:
            new_row = pd.DataFrame([{
                "Päivämäärä": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Nostaja": current_user,
                "Paino": float(w),
                "Toistot": int(r)
            }])
            updated_df = pd.concat([df_logs, new_row], ignore_index=True)
            conn.update(worksheet="Treeniloki", data=updated_df)
            st.success("Tallennettu! Päivitetään...")
            st.rerun()

with tab5:
    if st.button("LOGOUT"):
        st.session_state.clear()
        st.rerun()
