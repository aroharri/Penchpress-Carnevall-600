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
st.set_page_config(page_title="PENCH V2 - KARNEVAALIT", layout="wide")

# --- DATA ACCESS ---
try:
    SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
    BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    SCRIPT_URL = st.secrets["connections"]["gsheets"]["script_url"]
except Exception as e:
    st.error("Secrets uupuu! Varmista 'script_url' Streamlitin asetuksissa.")
    st.stop()

def load_sheet(name):
    cache_buster = int(time.time())
    url = f"{BASE_URL}{name}&cb={cache_buster}"
    try:
        response = requests.get(url, timeout=10)
        return pd.read_csv(StringIO(response.text))
    except:
        return pd.DataFrame()

# --- DATA LOAD ---
df_users = load_sheet("users")
df_log = load_sheet("logi")

if not df_log.empty:
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0.0)
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], dayfirst=True, errors='coerce')
if not df_users.empty:
    df_users.columns = df_users.columns.str.strip().str.lower()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_names = df_users['nimi'].tolist() if not df_users.empty else []
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU SISÄÄN", use_container_width=True):
        u_row = df_users[df_users['nimi'] == user_choice].iloc[0]
        if str(pin_input) == str(u_row['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_row.to_dict()
            st.rerun()
    st.stop()

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
    .big-val { font-size: 42px; text-align: center; color: #FF4B4B; font-weight: bold; margin-bottom: 0px; }
    .sub-val { font-size: 20px; text-align: center; color: #FFF; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    if not df_log.empty:
        latest = df_log.sort_values('pvm_dt').groupby('email').tail(1)
        total = latest['laskettu_ykkonen'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("NYT", f"{total:.2f} kg")
        c2.metric("TAVOITE", "600.00 kg")
        c3.metric("GAP", f"{600 - total:.2f} kg", delta_color="inverse")
        
        st.progress(min(1.0, total/600.0))
        
        # Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = total,
            gauge = {'axis': {'range': [500, 650]}, 'bar': {'color': "red"},
                     'threshold': {'line': {'color': "white", 'width': 4}, 'value': 600}}
        ))
        fig_gauge.update_layout(height=250, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)

# --- TAB 2: NOSTAJAT ---
with tab2:
    st.title("SQUAD")
    for _, u in df_users.iterrows():
        u_log = df_log[df_log['email'] == u['email']]
        p_max = u_log['laskettu_ykkonen'].max() if not u_log.empty else 0.0
        st.markdown(f"**{u['nimi']}** (PB: {p_max:.2f} kg / Tavoite: {u['tavoite']} kg)")
        st.divider()

# --- TAB 3: FEED ---
with tab3:
    st.title("THE FEED")
    if not df_log.empty:
        merged = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
        for _, r in merged.head(15).iterrows():
            st.markdown(f"**{r['nimi']}** • {r['kommentti']}")
            st.write(f"🏋️ {r['paino']}kg x {int(r['toistot'])} (1RM: **{r['laskettu_ykkonen']:.2f}kg**)")
            st.divider()

# --- TAB 4: MINÄ (Senior UX / Heatmap Version) ---
with tab4:
    st.markdown(f"### Tervehdys, {st.session_state.user['nimi'].title()}")
    
    # Alustetaan arvot
    if 'w_val' not in st.session_state: st.session_state.w_val = 100.0
    if 'r_val' not in st.session_state: st.session_state.r_val = 1
    if 'mood' not in st.session_state: st.session_state.mood = "✅ Perus"

    st.markdown("---")

    # SECTION 1: PAINO (Heatmap-painikkeet)
    st.markdown("#### 1. VALITSE PAINO (kg)")
    
    # Määritellään painot ja niille huumorivärit (Streamlitin painikkeissa ei ole suoraa CSS-väriä per nappi, 
    # joten käytetään visuaalista listaa ja korostetaan valittua)
    weight_options = list(range(90, 161, 5)) # 90, 95, 100... 160
    
    # Luodaan ruudukko (4 saraketta)
    cols = st.columns(4)
    for i, w in enumerate(weight_options):
        # Väriindikaattori tekstissä
        prefix = ""
        if w < 110: prefix = "⚪ "
        elif w < 130: prefix = "🟡 "
        elif w < 150: prefix = "🟠 "
        else: prefix = "🔴 "
        
        # Aktiivisen napin korostus
        is_active = "primary" if st.session_state.w_val == float(w) else "secondary"
        
        if cols[i % 4].button(f"{prefix}{w}", key=f"w_{w}", type=is_active, use_container_width=True):
            st.session_state.w_val = float(w)

    # Näytetään valittu paino isolla
    st.markdown(f"<div style='text-align:center; padding:10px;'>"
                f"<span style='font-size:42px; font-weight:900; color:#FF4B4B;'>{st.session_state.w_val} kg</span>"
                f"</div>", unsafe_allow_html=True)

    st.markdown("---")

    # SECTION 2: TOISTOT
    st.markdown("#### 2. TOISTOT")
    rep_cols = st.columns(6)
    rep_options = [1, 2, 3, 5, 8, 10]
    for i, r in enumerate(rep_options):
        btn_type = "primary" if st.session_state.r_val == r else "secondary"
        if rep_cols[i].button(f"{r}", key=f"r_{r}", type=btn_type, use_container_width=True):
            st.session_state.r_val = r

    st.markdown("---")

    # SECTION 3: TUNNELMA & SALI
    st.markdown("#### 3. TUNNELMA & SALI")
    
    f_col1, f_col2 = st.columns(2)
    # YEAH BUDDY on nyt Senior-tason valinta
    if f_col1.button("🔥 YEAH BUDDY!", use_container_width=True):
        st.session_state.mood = "YEAH BUDDY!"
    if f_col2.button("🧊 PIENTÄ JUMPPAA", use_container_width=True):
        st.session_state.mood = "Lähinnä tämmöstä pientä jumppailua (Niilo22)"
    
    gym = st.text_input("Missä rauta liikkui?", value="Keskus-Sali")

    # SECTION 4: TALLENNUS
    w_final = st.session_state.w_val
    r_final = st.session_state.r_val
    calculated_1rm = w_final if r_final == 1 else round(w_final / (1.0278 - 0.0278 * r_final), 2)
    
    # Dynaaminen huumoriteksti painon mukaan
    humor_label = ""
    if w_final >= 140: humor_label = "⚠️ VAROITUS: Titaania havaittu!"
    elif w_final >= 120: humor_label = "🚀 Nyt alkaa tuntuun!"
    else: humor_label = "✅ Hyvää työtä."

    st.markdown(f"<div style='text-align:center; color:#FF4B4B; font-weight:bold;'>{humor_label}</div>", unsafe_allow_html=True)
    st.write("")

    if st.button("TALLENNA SUORITUS", type="primary", use_container_width=True):
        payload = {
            "pvm": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "email": st.session_state.user['email'],
            "paino": float(w_final),
            "toistot": int(r_final),
            "laskettu_ykkonen": calculated_1rm,
            "kommentti": f"{st.session_state.mood} @ {gym}"
        }
        
        try:
            requests.post(SCRIPT_URL, json=payload, timeout=10)
            st.balloons()
            st.success(f"Tallennettu! 1RM ennuste: {calculated_1rm} kg")
            time.sleep(1.5)
            st.rerun()
        except:
            st.error("Yhteysvirhe tallennuksessa.")

    st.write("")
    if st.button("Kirjaudu ulos", key="logout_btn"):
        st.session_state.clear()
        st.rerun()
