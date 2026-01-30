# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2", layout="wide")

# --- DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOAD DATA SAFELY ---
def load_data():
    try:
        u = conn.read(worksheet="users", ttl=0)
        l = conn.read(worksheet="logi", ttl=0)
        s = conn.read(worksheet="settings", ttl=0)
        return u, l, s
    except Exception as e:
        st.error(f"DATA VIRHE: Varmista etta Sheets-valilehdet ovat: users, logi, settings. Virhe: {e}")
        st.stop()

df_users, df_log, df_settings = load_data()

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
            st.error("Vaara PIN")
    st.stop()

# --- CSS ---
st.markdown("""
<style>
    .lifter-card {
        background-color: #111;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; }
    .main .block-container { padding-bottom: 100px; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINA"])

# --- DASHBOARD ---
with tab1:
    st.title("SQUAD STATUS")
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0)
    current_total = df_log.groupby('email')['laskettu_ykkonen'].max().sum()
    goal = float(df_settings[df_settings['avain'] == 'ryhma_tavoite']['arvo'].values[0])
    
    c1, c2 = st.columns(2)
    c1.metric("YHTEISTULOS", f"{current_total:.1f} kg")
    c2.metric("GAP", f"{goal - current_total:.1f} kg", delta_color="inverse")

# --- NOSTAJAT (KORTIT) ---
with tab2:
    st.title("NOSTAJAT")
    for _, user in df_users.iterrows():
        u_logs = df_log[df_log['email'] == user['email']].sort_values('pvm')
        current_max = u_logs['laskettu_ykkonen'].max() if not u_logs.empty else 0
        
        with st.container():
            st.markdown(f"<div class='lifter-card'><h3>{user['nimi'].upper()}</h3></div>", unsafe_allow_html=True)
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.write(f"**Paras:** {current_max:.1f} kg")
                st.write(f"**Tavoite:** {user['tavoite']} kg")
            with col_b:
                if not u_logs.empty:
                    fig = px.line(u_logs, x='pvm', y='laskettu_ykkonen', markers=True)
                    fig.update_layout(height=150, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Nayta reenihistoria"):
                st.table(u_logs[['pvm', 'paino', 'toistot', 'fiilis']].iloc[::-1])

# --- FEED ---
with tab3:
    st.title("FEED")
    merged_feed = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm', ascending=False)
    for _, row in merged_feed.head(15).iterrows():
        st.markdown(f"**{row['nimi']}** • {row['fiilis']}")
        st.write(f"{row['paino']}kg x {row['toistot']} (1RM: {row['laskettu_ykkonen']}kg)")
        st.divider()

# --- USER (LOGGING) ---
with tab4:
    st.title(f"TERVE {st.session_state.user['nimi']}!")
    
    with st.container():
        st.subheader("MERKKAA REENI")
        w = st.number_input("Paino (kg)", step=2.5, value=100.0)
        r = st.number_input("Toistot", step=1, value=1)
        
        st.write("Fiilis:")
        f_cols = st.columns(5)
        options = ["🚀", "✅", "🥵", "💀", "🤕"]
        # Kaytetaan radio-nappia vaakatasossa fiilikselle
        fiilis = st.radio("Valitse fiilis", options, horizontal=True)
        
        if st.button("TALLENNA SUORITUS", use_container_width=True):
            one_rm = round(w * (1 + r/30.0), 1)
            new_row = pd.DataFrame([{
                "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "email": st.session_state.user['email'],
                "paino": w, "toistot": r, "laskettu_ykkonen": one_rm, "fiilis": fiilis
            }])
            conn.update(worksheet="logi", data=pd.concat([df_log, new_row], ignore_index=True))
            st.success(f"Tallennettu! 1RM oli {one_rm}kg")
            st.rerun()
            
    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
