# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import requests
from io import StringIO

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2", layout="wide")

# --- DATA ACCESS ---
SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

def load_sheet(name):
    url = BASE_URL + name
    response = requests.get(url)
    return pd.read_csv(StringIO(response.text))

# --- LOAD DATA ---
df_users = load_sheet("users")
df_log = load_sheet("logi")
df_users.columns = df_users.columns.str.strip().str.lower()
df_log.columns = df_log.columns.str.strip().str.lower()

# --- CALCULATIONS ---
# 1. Jokaisen nostajan TUOREIN laskettu ykkönen
df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
current_total = latest_lifts['laskettu_ykkonen'].sum()
group_goal = 600.0

# 2. Ryhmän historia (Yhteistulos ajan funktiona)
# Lasketaan jokaiselle lokimerkinnälle, mikä oli ryhmän sen hetkinen yhteistulos
history_list = []
unique_emails = df_users['email'].unique()
sorted_logs = df_log.sort_values('pvm_dt')

current_state = {email: 0 for email in unique_emails}
for _, row in sorted_logs.iterrows():
    current_state[row['email']] = row['laskettu_ykkonen']
    history_list.append({
        'pvm': row['pvm_dt'],
        'yhteistulos': sum(current_state.values())
    })
df_history = pd.DataFrame(history_list)

# 3. Tavoiteviivan generointi (Linear path)
start_date = datetime(2025, 12, 27)
end_date = datetime(2026, 12, 27)
today = datetime.now()

# Lasketaan tavoite tälle päivälle
total_days = (end_date - start_date).days
days_passed = (today - start_date).days
daily_target = 530 + (days_passed * (70/total_days))

# --- UI ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINA"])

with tab1:
    # KPI Kortit
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("SQUAD TOTAL NOW", f"{current_total:.1f} kg", delta=f"{current_total - daily_target:.1f} kg vs aikataulu")
    with c2:
        st.metric("GOAL", f"{group_goal:.0f} kg")
    with c3:
        st.metric("MATKAA JÄLJELLÄ", f"{group_goal - current_total:.1f} kg", delta_color="inverse")

    # Gauge Mittari
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_total,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [500, 650], 'tickwidth': 1},
            'bar': {'color': "red"},
            'steps': [
                {'range': [500, 600], 'color': "#222"},
                {'range': [600, 650], 'color': "#111"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 600
            }
        }
    ))
    fig_gauge.update_layout(height=350, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Aikasarja (The Path)
    st.subheader("THE PATH TO 600")
    fig_path = go.Figure()
    
    # Tavoiteviiva
    path_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    path_values = [530 + (i * (70/total_days)) for i in range(len(path_dates))]
    fig_path.add_trace(go.Scatter(x=path_dates, y=path_values, name="Tavoitekäyrä", line=dict(color='gray', dash='dash')))
    
    # Toteutuneet pallukat
    fig_path.add_trace(go.Scatter(x=df_history['pvm'], y=df_history['yhteistulos'], 
                                 mode='markers+lines', name="Toteuma", line=dict(color='red', width=3)))
    
    fig_path.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_path, use_container_width=True)

    # Nostajien taulukko
    st.subheader("SQUAD BREAKDOWN")
    
    breakdown_data = []
    for _, u in df_users.iterrows():
        latest = latest_lifts[latest_lifts['email'] == u['email']]
        val = latest['laskettu_ykkonen'].values[0] if not latest.empty else 0
        target = u['tavoite']
        breakdown_data.append({
            "Nostaja": u['nimi'],
            "Nyt (kg)": round(val, 1),
            "Tavoite (kg)": target,
            "Delta": round(val - target, 1)
        })
    
    df_breakdown = pd.DataFrame(breakdown_data)
    # Lisätään Total-rivi
    total_row = pd.DataFrame([{"Nostaja": "TOTAL", "Nyt (kg)": current_total, "Tavoite (kg)": df_users['tavoite'].sum(), "Delta": current_total - df_users['tavoite'].sum()}])
    df_breakdown = pd.concat([df_breakdown, total_row], ignore_index=True)
    
    st.table(df_breakdown)
