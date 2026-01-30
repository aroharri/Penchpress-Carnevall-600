# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
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
try:
    df_users = load_sheet("users")
    df_log = load_sheet("logi")
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    
    # PAKOTETAAN NUMEROKSI JA PUHDISTETAAN
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0)
    df_users['tavoite'] = pd.to_numeric(df_users['tavoite'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Datan lataus tai muunnos epäonnistui: {e}")
    st.stop()

# --- CALCULATIONS ---
df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
current_total = latest_lifts['laskettu_ykkonen'].sum()
group_goal = 600.0

# Ryhmän historia (Vikasietoinen versio)
history_list = []
unique_emails = df_users['email'].unique()
sorted_logs = df_log.sort_values('pvm_dt').dropna(subset=['pvm_dt'])

current_state = {email: 0.0 for email in unique_emails}
for _, row in sorted_logs.iterrows():
    if row['email'] in current_state:
        current_state[row['email']] = float(row['laskettu_ykkonen'])
        history_list.append({
            'pvm': row['pvm_dt'],
            'yhteistulos': sum(current_state.values())
        })

df_history = pd.DataFrame(history_list) if history_list else pd.DataFrame(columns=['pvm', 'yhteistulos'])

# Tavoitepolku 27.12.2025 -> 27.12.2026
start_date = datetime(2025, 12, 27)
end_date = datetime(2026, 12, 27)
today = datetime.now()
total_days = (end_date - start_date).days
days_passed = max(0, (today - start_date).days)
daily_target = 530 + (days_passed * (70/total_days))

# --- UI TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    
    # KPI KORTIT
    c1, c2, c3 = st.columns(3)
    c1.metric("SQUAD TOTAL", f"{current_total:.1f} kg", delta=f"{current_total - daily_target:.1f} kg vs aikataulu")
    c2.metric("TARGET", f"{group_goal:.0f} kg")
    c3.metric("GAP", f"{group_goal - current_total:.1f} kg", delta_color="inverse")

    # GAUGE
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_total,
        gauge = {
            'axis': {'range': [500, 650], 'tickwidth': 1},
            'bar': {'color': "red"},
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 600}
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_gauge, use_container_width=True)

    # PATH GRAPH
    st.subheader("THE PATH TO 600")
    fig_path = go.Figure()
    # Tavoiteviiva
    path_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    path_values = [530 + (i * (70/total_days)) for i in range(len(path_dates))]
    fig_path.add_trace(go.Scatter(x=path_dates, y=path_values, name="Tavoitekäyrä", line=dict(color='rgba(255,255,255,0.2)', dash='dash')))
    # Toteuma
    if not df_history.empty:
        fig_path.add_trace(go.Scatter(x=df_history['pvm'], y=df_history['yhteistulos'], mode='lines+markers', name="Toteuma", line=dict(color='red', width=4)))
    
    fig_path.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_path, use_container_width=True)

    # BREAKDOWN TABLE
    st.subheader("INDIVIDUAL STATUS")
    breakdown_list = []
    for _, u in df_users.iterrows():
        u_latest = latest_lifts[latest_lifts['email'] == u['email']]
        val = float(u_latest['laskettu_ykkonen'].values[0]) if not u_latest.empty else 0.0
        target = float(u['tavoite'])
        breakdown_list.append({
            "Nostaja": u['nimi'],
            "Nykyinen (kg)": val,
            "Tavoite (kg)": target,
            "Delta (kg)": round(val - target, 1)
        })
    
    df_br = pd.DataFrame(breakdown_list)
    # Total rivi
    total_row = pd.DataFrame([{"Nostaja": "--- TOTAL ---", "Nykyinen (kg)": current_total, "Tavoite (kg)": df_users['tavoite'].sum(), "Delta (kg)": current_total - df_users['tavoite'].sum()}])
    st.table(pd.concat([df_br, total_row], ignore_index=True))

# (Loput välilehdet: Nostajat, Feed, User pidetään ennallaan...)
