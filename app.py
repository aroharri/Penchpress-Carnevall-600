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

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; padding: 10px; z-index: 1000; justify-content: center; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
    .metric-card { background-color: #111; padding: 15px; border-radius: 10px; border: 1px solid #222; text-align: center; }
    .lifter-card { background-color: #1a1a1a; padding: 10px; border-radius: 8px; border-left: 5px solid #FF0000; margin-bottom: 10px; }
    .feed-item { background-color: #0c0c0c; padding: 8px; border-radius: 5px; border-bottom: 1px solid #222; margin-bottom: 5px; font-size: 0.85rem; }
    h1, h2, h3 { color: #FF0000 !important; font-family: 'Arial Black'; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=10)
def load_all_data():
    # Käytetään nimiä joissa ei ole ääkkösiä
    logs = conn.read(worksheet="logi")
    quests = conn.read(worksheet="quests")
    q_log = conn.read(worksheet="qlog")
    target_path = conn.read(worksheet="aikataulu")
    users_df = conn.read(worksheet="users")
    return logs, quests, q_log, target_path, users_df

try:
    df_logs, df_quests, df_q_log, df_path, df_users = load_all_data()
except Exception as e:
    st.error(f"Error loading sheets: {e}")
    st.stop()

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>⚡ LOGIN</h1>", unsafe_allow_html=True)
    # Haetaan nimet nostajat-taulukosta
    user_names = df_users['nimi'].tolist()
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    
    if st.button("KIRJAUDU"):
        correct_pin = str(df_users[df_users['nimi'] == user_choice]['PIN'].values[0])
        if pin_input == correct_pin:
            st.session_state.logged_in = True
            st.session_state.user_name = user_choice
            st.session_state.user_email = df_users[df_users['nimi'] == user_choice]['email'].values[0]
            st.rerun()
        else:
            st.error("Vaara PIN")
    st.stop()

# --- CALCULATIONS ---
# 1. Maksimit (Logi-välilehdeltä)
df_logs['paino'] = pd.to_numeric(df_logs['id'], errors='coerce').fillna(0) # Huom: tarkista onko 'id' tässä paino? Oletan paino-sarakkeen nimeksi jotain muuta jos 'id' on vain rivitunniste.
# Käytetään saraketta 'arvioitu_1rm' jos se on laskettu Sheetsissä, muuten lasketaan itse.
if 'arvioitu_1rm' in df_logs.columns:
    df_logs['1RM'] = pd.to_numeric(df_logs['arvioitu_1rm'], errors='coerce').fillna(0)
else:
    # Jos painoa ei ole nimetty, oletetaan että se on jossain sarakkeessa. Käytetään dummy-laskua tässä.
    df_logs['1RM'] = 0 

# Haetaan kunkin nostajan (emailin perusteella) paras 1RM
lifter_maxes = {}
for _, u in df_users.iterrows():
    u_email = u['email']
    u_name = u['nimi']
    max_val = df_logs[df_logs['nostaja_email'] == u_email]['1RM'].max()
    lifter_maxes[u_name] = max_val if pd.notnull(max_val) else 0.0

current_total = sum(lifter_maxes.values())

# --- UI TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 TILANNE", "📈 POLKU", "🏋️ NOSTO", "🎯 QUESTS", "👤 MINA"])

with tab1:
    st.markdown("<h1 style='text-align:center;'>TILANNEHUONE</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("NYT", f"{current_total:.1f} kg")
    c2.metric("TAVOITE", "600 kg")
    c3.metric("GAP", f"{600-current_total:.1f} kg")

    fig = go.Figure(go.Indicator(mode="gauge+number", value=current_total, gauge={'axis': {'range': [530, 600]}, 'bar': {'color': "red"}}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=220, margin=dict(t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⛓️ SQUAD STATUS")
    cols = st.columns(2)
    for i, (name, val) in enumerate(lifter_maxes.items()):
        cols[i%2].markdown(f'<div class="lifter-card"><small>{name}</small><br><b>{val:.1f} kg</b></div>', unsafe_allow_html=True)

with tab2:
    st.markdown("### THE PATH TO 600")
    fig_path = go.Figure()
    # Käytetään uusia sarakkenimiä 'pvm' ja 'tavoite_kg'
    fig_path.add_trace(go.Scatter(x=df_path['pvm'], y=df_path['tavoite_kg'], name="Target", line=dict(color='gray', dash='dot')))
    fig_path.add_trace(go.Scatter(x=[datetime.now()], y=[current_total], name="Now", mode="markers+text", text=["NOW"], marker=dict(color='red', size=12)))
    fig_path.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_path, use_container_width=True)

with tab3:
    st.markdown("### LOG LIFT")
    with st.form("lift_form"):
        # Huom: Sarakkeet Sheetsissä: pvm, nostaja_email, toistot, arvioitu_1rm, kommentti
        weight = st.number_input("Paino (kg)", step=2.5)
        reps = st.number_input("Toistot", step=1, min_value=1)
        comment = st.text_input("Kommentti")
        if st.form_submit_button("TALLENNA NOSTO"):
            one_rm = weight * (1 + reps/30.0)
            new_row = pd.DataFrame([{
                "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "nostaja_email": st.session_state.user_email,
                "toistot": reps,
                "arvioitu_1rm": one_rm,
                "kommentti": comment
            }])
            # Tallennus Sheetsiin
            updated_df = pd.concat([df_logs, new_row], ignore_index=True)
            conn.update(worksheet="Logi", data=updated_df)
            st.success("Tallennettu! Paivita sivu.")
            st.rerun()

with tab4:
    st.markdown("### QUESTS")
    # Sama logiikka kuin aiemmin, mutta worksheet "sidequest"
    for _, row in df_quests.iterrows():
        st.write(f"**{row['tehtava']}** - {row['pisteet']} pts")
        st.write(row['kuvaus'])
        st.divider()

with tab5:
    st.write(f"Nimi: {st.session_state.user_name}")
    st.write(f"Email: {st.session_state.user_email}")
    if st.button("LOGOUT"):
        st.session_state.clear()
        st.rerun()
