# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from io import StringIO
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2", layout="wide")

# --- DATA ACCESS (FORCE-LOAD FOR STABILITY) ---
# Käytetään tätä lukemiseen, jotta vältetään HTTP 400 -virheet
SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

def load_sheet(name):
    url = BASE_URL + name
    response = requests.get(url)
    return pd.read_csv(StringIO(response.text))

# Kirjoittamiseen tarvitaan tavallinen yhteys
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOAD DATA ---
try:
    df_users = load_sheet("users")
    df_log = load_sheet("logi")
    df_settings = load_sheet("settings")
    
    # Sarakkeiden siivous
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_settings.columns = df_settings.columns.str.strip().str.lower()
    
    # Pakotetaan numerot oikeaan muotoon
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0)
    df_log['paino'] = pd.to_numeric(df_log['paino'], errors='coerce').fillna(0)
    df_log['toistot'] = pd.to_numeric(df_log['toistot'], errors='coerce').fillna(0)
    df_users['tavoite'] = pd.to_numeric(df_users['tavoite'], errors='coerce').fillna(0)
    
except Exception as e:
    st.error(f"Datan lataus epäonnistui: {e}")
    st.stop()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_names = df_users['nimi'].tolist()
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU"):
        u_row = df_users[df_users['nimi'] == user_choice].iloc[0]
        if str(pin_input) == str(u_row['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_row.to_dict()
            st.rerun()
        else:
            st.error("Väärä PIN")
    st.stop()

# --- CALCULATIONS FOR DASHBOARD ---
df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
# Ryhmän nykyinen yhteistulos (viimeisin per nostaja)
latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
current_total = latest_lifts['laskettu_ykkonen'].sum()
group_goal = 600.0

# Ryhmän historiadata graafia varten
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
df_history = pd.DataFrame(history_list)

# Tavoiteviivan laskenta (27.12.2025 -> 27.12.2026, 530kg -> 600kg)
start_date = datetime(2025, 12, 27)
end_date = datetime(2026, 12, 27)
total_days = (end_date - start_date).days
days_passed = max(0, (datetime.now() - start_date).days)
daily_target = 530 + (days_passed * (70/total_days))

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .lifter-card { background-color: #111; padding: 15px; border-radius: 12px; border-left: 6px solid #FF4B4B; margin-bottom: 15px; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
</style>
""", unsafe_allow_html=True)

# --- APP LAYOUT ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("SQUAD TOTAL", f"{current_total:.2f} kg", delta=f"{current_total - daily_target:.2f} kg vs aikataulu")
    c2.metric("TARGET", f"{group_goal:.0f} kg")
    c3.metric("GAP", f"{group_goal - current_total:.2f} kg", delta_color="inverse")

    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_total,
        gauge = {
            'axis': {'range': [500, 650], 'tickwidth': 1},
            'bar': {'color': "red"},
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 600}
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Path graph
    st.subheader("THE PATH TO 600")
    fig_path = go.Figure()
    path_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    path_values = [530 + (i * (70/total_days)) for i in range(len(path_dates))]
    fig_path.add_trace(go.Scatter(x=path_dates, y=path_values, name="Target Path", line=dict(color='rgba(255,255,255,0.2)', dash='dash')))
    if not df_history.empty:
        fig_path.add_trace(go.Scatter(x=df_history['pvm'], y=df_history['yhteistulos'], mode='lines+markers', name="Actual", line=dict(color='red', width=4)))
    fig_path.update_layout(template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_path, use_container_width=True)

    # Individual Breakdown
    st.subheader("INDIVIDUAL STATUS")
    breakdown_list = []
    for _, u in df_users.iterrows():
        u_latest = latest_lifts[latest_lifts['email'] == u['email']]
        val = float(u_latest['laskettu_ykkonen'].values[0]) if not u_latest.empty else 0.0
        target = float(u['tavoite'])
        breakdown_list.append({"Nostaja": u['nimi'], "Nyt (kg)": round(val, 2), "Tavoite (kg)": round(target, 2), "Delta (kg)": round(val - target, 2)})
    df_br = pd.DataFrame(breakdown_list)
    total_row = pd.DataFrame([{"Nostaja": "--- TOTAL ---", "Nyt (kg)": round(current_total, 2), "Tavoite (kg)": round(df_users['tavoite'].sum(), 2), "Delta (kg)": round(current_total - df_users['tavoite'].sum(), 2)}])
    st.table(pd.concat([df_br, total_row], ignore_index=True))

# --- TAB 2: NOSTAJAT ---
with tab2:
    st.title("NOSTAJAT")
    for _, user in df_users.iterrows():
        u_logs = df_log[df_log['email'] == user['email']].sort_values('pvm_dt')
        current_max = u_logs['laskettu_ykkonen'].max() if not u_logs.empty else 0.0
        with st.container():
            st.markdown(f"<div class='lifter-card'><h3>{user['nimi'].upper()}</h3></div>", unsafe_allow_html=True)
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.metric("Paras 1RM", f"{current_max:.2f} kg")
                st.write(f"**Tavoite:** {user['tavoite']} kg")
            with col_b:
                if not u_logs.empty:
                    fig_u = px.line(u_logs, x='pvm_dt', y='laskettu_ykkonen', markers=True, color_discrete_sequence=['#FF4B4B'])
                    fig_u.update_layout(height=150, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_u, use_container_width=True)
            with st.expander("Reenihistoria"):
                st.table(u_logs[['pvm', 'paino', 'toistot', 'kommentti']].iloc[::-1])

# --- TAB 3: FEED ---
with tab3:
    st.title("THE FEED")
    merged_feed = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
    for _, row in merged_feed.head(20).iterrows():
        st.markdown(f"**{row['nimi']}** • {row['kommentti']}")
        st.write(f"🏋️ {row['paino']}kg x {int(row['toistot'])} (1RM: **{row['laskettu_ykkonen']:.2f}kg**)")
        st.caption(f"{row['pvm']}")
        st.divider()

# --- TAB 4: MINÄ (USER LOGGING) ---
with tab4:
    st.title(f"TERVE {st.session_state.user['nimi']}!")
    with st.container():
        st.subheader("MERKKAA REENI")
        w = st.number_input("Paino (kg)", step=2.5, value=100.0)
        r = st.number_input("Toistot", step=1, value=1)
        st.write("Miten meni?")
        kommentit = ["🚀 Kevyttä", "✅ Perus", "🥵 Tiukka", "💀 Kuolema", "🤕 Rikki"]
        kommentti = st.radio("Valitse fiilis", kommentit, horizontal=True)
        if st.button("TALLENNA SUORITUS", use_container_width=True):
            one_rm = round(w * (1 + r/30.0), 2)
            new_row = pd.DataFrame([{"pvm": datetime.now().strftime("%Y-%m-%d %H:%M"), "email": st.session_state.user['email'], "paino": w, "toistot": r, "laskettu_ykkonen": one_rm, "kommentti": kommentti}])
            # Kirjoittaminen
            conn.update(worksheet="logi", data=pd.concat([df_log.drop(columns=['pvm_dt']), new_row], ignore_index=True))
            st.balloons()
            st.success(f"Tallennettu! 1RM: {one_rm}kg")
            st.rerun()
    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
