# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from io import StringIO
import time

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2", layout="wide")

# --- DATA ACCESS ---
try:
    SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
    BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    SCRIPT_URL = st.secrets["connections"]["gsheets"]["script_url"]
except Exception as e:
    st.error("Secrets tai URL-asetus puuttuu!")
    st.stop()

def load_sheet(name):
    cache_buster = int(time.time())
    url = f"{BASE_URL}{name}&cb={cache_buster}"
    response = requests.get(url)
    return pd.read_csv(StringIO(response.text)) if response.status_code == 200 else pd.DataFrame()

# --- LOAD DATA ---
try:
    df_users = load_sheet("users")
    df_log = load_sheet("logi")
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0.0)
    df_log['paino'] = pd.to_numeric(df_log['paino'], errors='coerce').fillna(0.0)
    df_log['toistot'] = pd.to_numeric(df_log['toistot'], errors='coerce').fillna(0)
    df_users['tavoite'] = pd.to_numeric(df_users['tavoite'], errors='coerce').fillna(0.0)
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
except Exception as e:
    st.error(f"Datan latausvirhe: {e}")
    st.stop()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_names = df_users['nimi'].tolist() if not df_users.empty else []
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU", use_container_width=True):
        u_row = df_users[df_users['nimi'] == user_choice].iloc[0]
        if str(pin_input) == str(u_row['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_row.to_dict()
            st.rerun()
        else:
            st.error("Väärä PIN")
    st.stop()

# --- CALCS ---
latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
current_total = latest_lifts['laskettu_ykkonen'].sum()
group_goal = 600.0

# History for path
history_list = []
unique_emails = df_users['email'].unique()
sorted_logs = df_log.sort_values('pvm_dt').dropna(subset=['pvm_dt'])
current_state = {email: 0.0 for email in unique_emails}
for _, row in sorted_logs.iterrows():
    if row['email'] in current_state:
        current_state[row['email']] = float(row['laskettu_ykkonen'])
        history_list.append({'pvm': row['pvm_dt'], 'yhteistulos': sum(current_state.values())})
df_history = pd.DataFrame(history_list)

# Dates
start_date = datetime(2025, 12, 27)
end_date = datetime(2026, 12, 27)
total_days = (end_date - start_date).days
days_passed = max(0, (datetime.now() - start_date).days)
daily_target = 530 + (days_passed * (70/total_days))

# --- CSS ---
st.markdown("<style>.stApp { background-color: #050505; } .lifter-card { background-color: #111; padding: 15px; border-radius: 12px; border-left: 6px solid #FF4B4B; margin-bottom: 15px; } .stTabs [data-baseweb='tab-list'] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; } .main .block-container { padding-bottom: 120px; }</style>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("SQUAD TOTAL", f"{current_total:.2f} kg", delta=f"{current_total - daily_target:.2f} kg vs aikataulu")
    c2.metric("TARGET", f"{group_goal:.0f} kg")
    c3.metric("GAP", f"{group_goal - current_total:.2f} kg", delta_color="inverse")

    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = current_total,
        gauge = {'axis': {'range': [500, 650]}, 'bar': {'color': "red"},
                 'threshold': {'line': {'color': "white", 'width': 4}, 'value': 600}}
    ))
    fig_gauge.update_layout(height=250, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.subheader("THE PATH TO 600")
    fig_path = go.Figure()
    path_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    path_values = [530 + (i * (70/total_days)) for i in range(len(path_dates))]
    fig_path.add_trace(go.Scatter(x=path_dates, y=path_values, name="Target", line=dict(color='rgba(255,255,255,0.2)', dash='dash')))
    if not df_history.empty:
        fig_path.add_trace(go.Scatter(x=df_history['pvm'], y=df_history['yhteistulos'], mode='lines+markers', name="Actual", line=dict(color='red', width=4)))
    fig_path.update_layout(template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_path, use_container_width=True)

    st.subheader("INDIVIDUAL STATUS")
    br_list = []
    for _, u in df_users.iterrows():
        u_lat = latest_lifts[latest_lifts['email'] == u['email']]
        val = float(u_lat['laskettu_ykkonen'].values[0]) if not u_lat.empty else 0.0
        br_list.append({"Nostaja": u['nimi'], "Nyt (kg)": round(val, 2), "Tavoite (kg)": round(u['tavoite'], 2), "Delta (kg)": round(val - u['tavoite'], 2)})
    df_br = pd.DataFrame(br_list)
    total_row = pd.DataFrame([{"Nostaja": "--- TOTAL ---", "Nyt (kg)": round(current_total, 2), "Tavoite (kg)": round(df_users['tavoite'].sum(), 2), "Delta (kg)": round(current_total - df_users['tavoite'].sum(), 2)}])
    st.table(pd.concat([df_br, total_row], ignore_index=True))

with tab2:
    st.title("NOSTAJAT")
    for _, user in df_users.iterrows():
        u_logs = df_log[df_log['email'] == user['email']].sort_values('pvm_dt')
        cur_max = u_logs['laskettu_ykkonen'].max() if not u_logs.empty else 0.0
        with st.container():
            st.markdown(f"<div class='lifter-card'><h3>{user['nimi'].upper()}</h3></div>", unsafe_allow_html=True)
            ca, cb = st.columns([1, 2])
            ca.metric("Paras 1RM", f"{cur_max:.2f} kg")
            if not u_logs.empty:
                fu = px.line(u_logs, x='pvm_dt', y='laskettu_ykkonen', markers=True, color_discrete_sequence=['#FF4B4B'])
                fu.update_layout(height=150, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                cb.plotly_chart(fu, use_container_width=True)
            with st.expander("Historia"):
                st.table(u_logs[['pvm', 'paino', 'toistot', 'kommentti']].iloc[::-1])

with tab3:
    st.title("THE FEED")
    if not df_log.empty:
        merged_feed = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
        for _, row in merged_feed.head(20).iterrows():
            st.markdown(f"**{row['nimi']}** • {row['kommentti']}")
            st.write(f"🏋️ {row['paino']}kg x {int(row['toistot'])} (1RM: **{row['laskettu_ykkonen']:.2f}kg**)")
            st.divider()

with tab4:
    st.title(f"TERVE {st.session_state.user['nimi']}!")
    with st.container():
        st.subheader("MERKKAA REENI")
        w = st.number_input("Paino (kg)", step=2.5, value=100.0)
        r = st.number_input("Toistot", step=1, value=1)
        kom_opt = ["🚀 Kevyttä", "✅ Perus", "🥵 Tiukka", "💀 Kuolema", "🤕 Rikki"]
        kom = st.radio("Fiilis", kom_opt, horizontal=True)
        if st.button("TALLENNA SUORITUS", use_container_width=True):
            # KORJATTU RM-MATEMATIIKKA
            if r == 1:
                one_rm = float(w)
            else:
                one_rm = round(w / (1.0278 - 0.0278 * r), 2)
            
            payload = {
                "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "email": st.session_state.user['email'],
                "paino": float(w),
                "toistot": int(r),
                "laskettu_ykkonen": one_rm,
                "kommentti": kom
            }
            try:
                requests.post(SCRIPT_URL, json=payload)
                st.balloons()
                st.success(f"Tallennettu! 1RM: {one_rm}kg")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Tallennus epäonnistui: {e}")
