# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH CARNEVALL 600", layout="centered")

# --- DATABASE CONNECTION ---
try:
    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Spreadsheet URL missing from Secrets!")
    st.stop()

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

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

USERS = st.secrets["users"]

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>⚡ LOGIN</h1>", unsafe_allow_html=True)
    u_list = list(USERS.keys())
    user_choice = st.selectbox("VALITSE NOSTAJA", u_list)
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU"):
        if pin_input == USERS[user_choice]:
            st.session_state.logged_in = True
            st.session_state.user = user_choice
            st.rerun()
        else:
            st.error("Vaara PIN")
    st.stop()

# --- DATA LOADING ---
try:
    df_logs = conn.read(spreadsheet=spreadsheet_url, worksheet="Logi", ttl=0)
    df_quests = conn.read(spreadsheet=spreadsheet_url, worksheet="Quests", ttl=0)
    df_q_log = conn.read(spreadsheet=spreadsheet_url, worksheet="QuestLog", ttl=0)
except Exception as e:
    st.error("Data Load Error. Check Sheets names.")
    st.stop()

# --- CALCULATIONS ---
# 1. Maksimit
df_logs['Paino'] = pd.to_numeric(df_logs['Paino'], errors='coerce').fillna(0)
df_logs['Toistot'] = pd.to_numeric(df_logs['Toistot'], errors='coerce').fillna(0)
df_logs['Max'] = df_logs['Paino'] * (1 + df_logs['Toistot'] / 30.0)
lifter_maxes = df_logs.groupby('Nostaja')['Max'].max().to_dict()
for name in USERS.keys():
    if name not in lifter_maxes: lifter_maxes[name] = 0.0
current_total = sum(lifter_maxes.values())

# 2. Feedi-data (Yhdistetään nostot ja questit)
feed_entries = []
for _, row in df_logs.iterrows():
    feed_entries.append({
        'pvm': row['Pvm'], 
        'txt': f"🏋️ **{row['Nostaja']}** nosti **{row['Paino']}kg x {int(row['Toistot'])}** (Max: {row['Max']:.1f}kg)"
    })
for _, row in df_q_log.iterrows():
    q_name = df_quests[df_quests['ID'] == row['QuestID']]['Tehtava'].values[0] if not df_quests.empty else "Quest"
    feed_entries.append({
        'pvm': row['Pvm'], 
        'txt': f"🔥 **{row['Nostaja']}** suoritti: **{q_name}**"
    })
# Lajitellaan uusin ensin
feed_entries = sorted(feed_entries, key=lambda x: str(x['pvm']), reverse=True)

# --- UI TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 TILANNE", "📈 POLKU", "🏋️ NOSTO", "🎯 QUESTS", "👤 MINA"])

with tab1:
    st.markdown("<h1 style='text-align:center;'>TILANNEHUONE</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><small>NYT</small><br><b style="color:red;font-size:1.2rem;">{current_total:.1f}</b></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><small>TAVOITE</small><br><b style="font-size:1.2rem;">600.0</b></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><small>GAP</small><br><b style="font-size:1.2rem;">{600-current_total:.1f}</b></div>', unsafe_allow_html=True)

    fig = go.Figure(go.Indicator(mode="gauge+number", value=current_total, gauge={'axis': {'range': [500, 600]}, 'bar': {'color': "red"}}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=220, margin=dict(t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⛓️ SQUAD STATUS")
    cols = st.columns(2)
    for i, (name, val) in enumerate(lifter_maxes.items()):
        cols[i%2].markdown(f'<div class="lifter-card"><small>{name}</small><br><b>{val:.1f} kg</b></div>', unsafe_allow_html=True)

    st.markdown("### 📢 FEED")
    for entry in feed_entries[:10]: # Näytetään 10 uusinta
        st.markdown(f'<div class="feed-item"><small>{entry["pvm"]}</small><br>{entry["txt"]}</div>', unsafe_allow_html=True)

with tab3:
    st.markdown("### MERKKAA NOSTO")
    with st.form("lift_form", clear_on_submit=True):
        w = st.number_input("Paino (kg)", step=2.5, min_value=0.0)
        r = st.number_input("Toistot", step=1, min_value=1)
        if st.form_submit_button("TALLENNA"):
            new_row = pd.DataFrame([{"Pvm": datetime.now().strftime("%d.%m. %H:%M"), "Nostaja": st.session_state.user, "Paino": w, "Toistot": r}])
            updated_df = pd.concat([df_logs, new_row], ignore_index=True)
            if 'Max' in updated_df.columns: updated_df = updated_df.drop(columns=['Max'])
            conn.update(spreadsheet=spreadsheet_url, worksheet="Logi", data=updated_df)
            st.success("Tallennettu! Paivita sivu.")
            st.rerun()

with tab4:
    st.markdown("### 🛡️ SIDEQUESTS")
    done_quests = df_q_log[df_q_log['Nostaja'] == st.session_state.user]['QuestID'].astype(int).tolist()
    for _, row in df_quests.iterrows():
        q_id = int(row['ID'])
        is_done = q_id in done_quests
        with st.expander(f"{'✅' if is_done else '🔳'} {row['Tehtava']} (+{row['Pisteet']} pts)"):
            st.write(row['Kuvaus'])
            if not is_done:
                if st.button(f"Mark Done: {q_id}", key=f"q_{q_id}"):
                    new_q = pd.DataFrame([{"Pvm": datetime.now().strftime("%d.%m. %H:%M"), "Nostaja": st.session_state.user, "QuestID": q_id, "Status": "Done"}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="QuestLog", data=pd.concat([df_q_log, new_q], ignore_index=True))
                    st.rerun()

with tab5:
    st.write(f"Kayttaja: {st.session_state.user}")
    if st.button("LOGOUT"):
        st.session_state.clear()
        st.rerun()
