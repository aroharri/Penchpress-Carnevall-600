# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2", layout="wide")

# --- DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    return conn.read(worksheet=sheet_name, ttl=0)

# --- LOAD DATA ---
try:
    df_users = get_data("users")
    df_log = get_data("logi")
    df_settings = get_data("settings")
except Exception as e:
    st.error("Sheets-yhteys uupuu. Varmista välilehtien nimet.")
    st.stop()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_name = st.selectbox("VALITSE NOSTAJA", df_users['nimi'].tolist())
    pin = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU"):
        u_data = df_users[df_users['nimi'] == user_name].iloc[0]
        if str(pin) == str(u_data['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_data.to_dict()
            st.rerun()
        else:
            st.error("Väärä PIN")
    st.stop()

# --- APP LAYOUT ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "🏋️ NOSTAJAT", "📱 FEEDI", "👤 USER"])

# Lasketaan kunkin nostajan paras tulos
df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce')
max_lifts = df_log.groupby('email')['laskettu_ykkonen'].max().reset_index()
df_status = df_users.merge(max_lifts, on='email', how='left').fillna(0)
current_total = df_status['laskettu_ykkonen'].sum()
goal = float(df_settings[df_settings['avain'] == 'ryhma_tavoite']['arvo'].values[0])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.title("SQUAD STATUS")
    c1, c2, c3 = st.columns(3)
    c1.metric("NYKYINEN YHTEISTULOS", f"{current_total:.1f} kg")
    c2.metric("TAVOITE", f"{goal:.1f} kg")
    c3.metric("PUUTTUU", f"{goal - current_total:.1f} kg")

    # Mittari
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_total,
        gauge = {'axis': {'range': [500, 600]}, 'bar': {'color': "red"}},
        title = {'text': "Matka kohti 600kg"}
    ))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: NOSTAJAT ---
with tab2:
    st.title("NOSTAJA-ANALYTIIKKA")
    valittu_u = st.selectbox("VALITSE NOSTAJA TARKASTELUUN", df_users['nimi'].tolist())
    u_email = df_users[df_users['nimi'] == valittu_u]['email'].values[0]
    
    u_logs = df_log[df_log['email'] == u_email].sort_values('pvm')
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.subheader("Nykytilanne")
        current_max = u_logs['laskettu_ykkonen'].max() if not u_logs.empty else 0
        u_goal = df_users[df_users['nimi'] == valittu_u]['tavoite'].values[0]
        st.write(f"**Paras 1RM:** {current_max:.1f} kg")
        st.write(f"**Tavoite:** {u_goal} kg")
    
    with col_b:
        if not u_logs.empty:
            fig_progress = px.line(u_logs, x='pvm', y='laskettu_ykkonen', title="Kehityskäyrä (laskettu 1RM)")
            st.plotly_chart(fig_progress, use_container_width=True)

# --- TAB 3: FEEDI ---
with tab3:
    st.title("THE PENCH FEED")
    feed_data = df_log.sort_values('pvm', ascending=False).merge(df_users[['email', 'nimi']], on='email')
    for _, row in feed_data.head(20).iterrows():
        with st.container():
            st.markdown(f"**{row['nimi']}** • {row['pvm']}")
            st.write(f"🏋️ {row['paino']}kg x {row['toistot']} (1RM: **{row['laskettu_ykkonen']:.1f}kg**)")
            if row['kommentti']: st.caption(f"💬 {row['kommentti']}")
            st.divider()

# --- TAB 4: USER ---
with tab4:
    st.title(f"TERVE, {st.session_state.user['nimi']}!")
    
    with st.expander("➕ TALLENNA UUSI REENI"):
        with st.form("lift_form"):
            w = st.number_input("Paino (kg)", min_value=0.0, step=2.5)
            r = st.number_input("Toistot", min_value=1, step=1)
            c = st.text_input("Kommentti")
            if st.form_submit_button("TALLENNA"):
                # Brzycki 1RM
                one_rm = w * (1 + r/30.0)
                new_row = pd.DataFrame([{
                    "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "email": st.session_state.user['email'],
                    "paino": w,
                    "toistot": r,
                    "laskettu_ykkonen": round(one_rm, 1),
                    "kommentti": c
                }])
                conn.update(worksheet="logi", data=pd.concat([df_log, new_row], ignore_index=True))
                st.success("Tallennettu! Päivitä sivu.")
                st.rerun()

    if st.button("KIRJAUDU ULOS"):
        st.session_state.clear()
        st.rerun()
