# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH CARNEVALL 600", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CSS (Puhdas tyyli) ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; padding: 10px; z-index: 1000; justify-content: center; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
    .metric-card { background-color: #111; padding: 15px; border-radius: 10px; border: 1px solid #222; text-align: center; }
    .lifter-card { background-color: #1a1a1a; padding: 10px; border-radius: 8px; border-left: 5px solid #FF0000; margin-bottom: 10px; }
    h1, h2, h3 { color: #FF0000 !important; font-family: 'Arial Black'; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=5)
def load_all_data():
    # Kaytetaan tasan niita nimia jotka annoit
    l = conn.read(worksheet="logi")
    u = conn.read(worksheet="users")
    q = conn.read(worksheet="quests")
    ql = conn.read(worksheet="qlog")
    path = conn.read(worksheet="aikataulu")
    return l, u, q, ql, path

try:
    df_log, df_users, df_quests, df_qlog, df_path = load_all_data()
except Exception as e:
    st.error(f"Virhe ladattaessa dataa: {e}")
    st.stop()

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>⚡ LOGIN</h1>", unsafe_allow_html=True)
    user_names = df_users['nimi'].tolist()
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    
    if st.button("KIRJAUDU"):
        # PIN on users-taulukossa
        user_row = df_users[df_users['nimi'] == user_choice]
        correct_pin = str(user_row['pin'].values[0])
        if pin_input == correct_pin:
            st.session_state.logged_in = True
            st.session_state.user_name = user_choice
            st.session_state.user_email = user_row['email'].values[0]
            st.rerun()
        else:
            st.error("Vaara PIN")
    st.stop()

# --- CALCULATIONS ---
# Lasketaan kunkin nostajan paras 1RM (arvioitu_1rm sarakkeesta)
df_log['arvioitu_1rm'] = pd.to_numeric(df_log['arvioitu_1rm'], errors='coerce').fillna(0)
lifter_maxes = {}
for _, u in df_users.iterrows():
    m = df_log[df_log['nostaja_email'] == u['email']]['arvioitu_1rm'].max()
    lifter_maxes[u['nimi']] = m if pd.notnull(m) else 0.0

current_total = sum(lifter_maxes.values())

# --- UI TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 TILANNE", "📈 POLKU", "🏋️ NOSTO", "🎯 QUESTS", "👤 MINA"])

with tab1:
    st.markdown("<h1 style='text-align:center;'>TILANNEHUONE</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("NYT", f"{current_total:.1f} kg")
    c2.metric("TAVOITE", "600 kg")
    c3.metric("GAP", f"{600-current_total:.1f} kg")

    fig = go.Figure(go.Indicator(mode="gauge+number", value=current_total, gauge={'axis': {'range': [500, 600]}, 'bar': {'color': "red"}}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=250)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⛓️ SQUAD 1RM")
    cols = st.columns(2)
    for i, (name, val) in enumerate(lifter_maxes.items()):
        cols[i%2].markdown(f'<div class="lifter-card"><small>{name}</small><br><b>{val:.1f} kg</b></div>', unsafe_allow_html=True)

with tab2:
    st.markdown("### THE PATH TO 600")
    # Kaytetaan aikataulu-valilehden sarakkeita pvm ja tavoite
    fig_path = go.Figure()
    fig_path.add_trace(go.Scatter(x=df_path['pvm'], y=df_path['tavoite'], name="Target", line=dict(color='gray', dash='dot')))
    fig_path.add_trace(go.Scatter(x=[datetime.now()], y=[current_total], name="Now", mode="markers+text", text=["NYT"], marker=dict(color='red', size=12)))
    fig_path.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_path, use_container_width=True)

with tab3:
    st.markdown("### LOG LIFT")
    with st.form("lift_form", clear_on_submit=True):
        weight = st.number_input("Paino (kg)", step=2.5, min_value=0.0)
        reps = st.number_input("Toistot", step=1, min_value=1)
        comment = st.text_input("Kommentti")
        if st.form_submit_button("TALLENNA NOSTO"):
            one_rm = weight * (1 + reps/30.0)
            # Luodaan uusi rivi Logi-valilehdelle
            new_row = pd.DataFrame([{
                "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "nostaja_email": st.session_state.user_email,
                "paino_kg": weight,
                "toistot_kpl": reps,
                "arvioitu_1rm": one_rm,
                "kommentti": comment
            }])
            conn.update(worksheet="logi", data=pd.concat([df_log, new_row], ignore_index=True))
            st.success("Tallennettu!")
            st.rerun()

with tab4:
    st.markdown("### QUESTS")
    for _, row in df_quests.iterrows():
        st.info(f"**{row['tehtava']}** ({row['pisteet']} pts)\n\n{row['kuvaus']}")

with tab5:
    st.markdown(f"### TERVE, {st.session_state.user_name.upper()}!")
    # Nayta profiilikuva jos URL on olemassa
    u_row = df_users[df_users['nimi'] == st.session_state.user_name]
    img_url = u_row['profiilikuva'].values[0]
    if pd.notnull(img_url) and str(img_url).startswith('http'):
        st.image(img_url, width=150)
    
    if st.button("LOGOUT"):
        st.session_state.clear()
        st.rerun()
