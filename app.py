# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from io import StringIO
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="PENCH KARNEVAALIT", layout="wide")

# --- DATA ACCESS ---
try:
    SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
    BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    SCRIPT_URL = st.secrets["connections"]["gsheets"]["script_url"]
except Exception as e:
    st.error("Secrets uupuu! Tarkista asetukset.")
    st.stop()

def load_sheet(name):
    cache_buster = int(time.time())
    url = f"{BASE_URL}{name}&cb={cache_buster}"
    try:
        response = requests.get(url, timeout=10)
        return pd.read_csv(StringIO(response.text))
    except:
        return pd.DataFrame()

# --- DATA PREP ---
df_users = load_sheet("users")
df_log = load_sheet("logi")

# Siivous ja tyypitys
if not df_users.empty:
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_users['tavoite'] = pd.to_numeric(df_users['tavoite'], errors='coerce').fillna(0)

if not df_log.empty:
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0.0)
    df_log['paino'] = pd.to_numeric(df_log['paino'], errors='coerce').fillna(0.0)
    df_log['toistot'] = pd.to_numeric(df_log['toistot'], errors='coerce').fillna(0)
    # Parsitaan pvm (oletetaan format dd.mm.yyyy HH:MM tai vastaava)
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], dayfirst=True, errors='coerce')

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

# --- CSS (DARK MODE & CARDS) ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #fff; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
    
    /* Nostajakortit */
    .lifter-card {
        background-color: #161616;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .lifter-stat { font-size: 14px; color: #888; }
    .lifter-val { font-size: 18px; font-weight: bold; color: #fff; }
    
    /* Feed */
    .feed-item {
        background-color: #111;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #222;
    }
    .feed-time { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; }
    .feed-header { font-size: 16px; font-weight: bold; color: #FF4B4B; }
    .feed-loc { font-size: 13px; color: #aaa; font-style: italic; }
    .feed-result { font-size: 20px; font-weight: 800; color: #fff; margin-top: 5px; }
    
    /* Minä */
    .big-val { font-size: 42px; text-align: center; color: #FF4B4B; font-weight: bold; margin-bottom: 0px; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- TAB 1: DASHBOARD (THE WAR ROOM) ---
with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    
    if not df_log.empty:
        # 1. NYKYTILANNE (Latest per user)
        latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
        current_total = latest_lifts['laskettu_ykkonen'].sum()
        target_final = 600.0
        
        # KPI KORTIT
        c1, c2, c3 = st.columns(3)
        c1.metric("NYKYINEN YHTEISTULOS", f"{current_total:.1f} kg")
        c2.metric("TAVOITE (27.12.26)", f"{target_final:.0f} kg")
        c3.metric("MATKAA JÄLJELLÄ", f"{target_final - current_total:.1f} kg", delta_color="inverse")

        # GAUGE (500-650kg)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_total,
            gauge = {
                'axis': {'range': [500, 650], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#FF4B4B"},
                'bgcolor': "black",
                'borderwidth': 2,
                'bordercolor': "#333",
                'steps': [
                    {'range': [500, 600], 'color': "#222"},
                    {'range': [600, 650], 'color': "#1a1a1a"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 600
                }
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig_gauge, use_container_width=True)

        # LINE GRAPH (THE PATH)
        st.subheader("THE PATH TO 600")
        
        # Aikajanat
        start_date = datetime(2025, 12, 27)
        end_date = datetime(2026, 12, 27)
        
        # Tavoiteviiva (Lineaarinen)
        dates_target = pd.date_range(start=start_date, end=end_date, freq='D')
        start_val = 530
        end_val = 600
        # Lineaarinen interpolaatio
        values_target = [start_val + (end_val - start_val) * (i / len(dates_target)) for i in range(len(dates_target))]
        
        # Toteutunut käyrä (Sum of latest per timestamp)
        # 1. Järjestetään kaikki logit
        sorted_logs = df_log.sort_values('pvm_dt').dropna(subset=['pvm_dt'])
        sorted_logs = sorted_logs[sorted_logs['pvm_dt'] >= start_date] # Vain startin jälkeiset
        
        history_points = []
        user_states = {u: 0.0 for u in df_users['email'].unique()} # Alustus
        
        # Jos meillä on pohjatietoja ennen 27.12.25, pitäisi ne hakea tähän "pohjalle",
        # mutta oletetaan nyt että kasvu alkaa 0:sta tai ekasta logista.
        # Parempi tapa: Asetetaan alkutilanteeksi n. 530 (tai lasketaan se jos dataa on).
        
        for _, row in sorted_logs.iterrows():
            user_states[row['email']] = row['laskettu_ykkonen']
            current_squad_sum = sum(user_states.values())
            history_points.append({'date': row['pvm_dt'], 'total': current_squad_sum})
            
        df_hist = pd.DataFrame(history_points)

        fig_line = go.Figure()
        
        # Tavoite (Katkoviiva)
        fig_line.add_trace(go.Scatter(
            x=dates_target, y=values_target,
            mode='lines',
            name='Tavoiteura (Linear)',
            line=dict(color='gray', dash='dash')
        ))
        
        # Toteuma (Pallukat)
        if not df_hist.empty:
            fig_line.add_trace(go.Scatter(
                x=df_hist['date'], y=df_hist['total'],
                mode='lines+markers',
                name='Toteuma',
                line=dict(color='#FF4B4B', width=3),
                marker=dict(size=8)
            ))

        fig_line.update_layout(
            template="plotly_dark",
            xaxis_title="Päivämäärä",
            yaxis_title="Yhteistulos (kg)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_range=[start_date, end_date],
            yaxis_range=[500, 620]
        )
        st.plotly_chart(fig_line, use_container_width=True)


# --- TAB 2: NOSTAJAT (KORTIT) ---
with tab2:
    st.title("SQUAD ROSTER")
    
    for _, u in df_users.iterrows():
        # Datan haku
        u_logs = df_log[df_log['email'] == u['email']].sort_values('pvm_dt', ascending=False)
        
        latest_rm = 0.0
        workouts_count = len(u_logs)
        if not u_logs.empty:
            latest_rm = u_logs.iloc[0]['laskettu_ykkonen']
            
        target = u['tavoite']
        delta = target - latest_rm
        
        # KORTTI UI
        with st.container():
            st.markdown(f"""
            <div class='lifter-card'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <h2 style='margin:0; color:#FF4B4B;'>{u['nimi'].upper()}</h2>
                    <span style='background:#333; padding:5px 10px; border-radius:5px; font-size:12px;'>{workouts_count} REENIÄ</span>
                </div>
                <hr style='border-color:#333; margin:10px 0;'>
                <div style='display:flex; justify-content:space-between; text-align:center;'>
                    <div><div class='lifter-stat'>Viimeisin 1RM</div><div class='lifter-val'>{latest_rm:.1f} kg</div></div>
                    <div><div class='lifter-stat'>Tavoite</div><div class='lifter-val'>{target:.0f} kg</div></div>
                    <div><div class='lifter-stat'>Matkaa</div><div class='lifter-val' style='color:{"#FF4B4B" if delta > 0 else "#0f0"}'>{delta:+.1f} kg</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # EXPANDER: HISTORIA
            with st.expander(f"Näytä historia ({u['nimi']})"):
                if not u_logs.empty:
                    # Muotoillaan taulukko nätiksi
                    display_df = u_logs[['pvm', 'paino', 'toistot', 'laskettu_ykkonen', 'kommentti']].copy()
                    display_df.columns = ['Pvm & Aika', 'Rauta (kg)', 'Toistot', '1RM (kg)', 'Kommentti / Sali']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Ei vielä kirjattuja suorituksia.")

# --- TAB 3: FEED (DETAIL LEVEL) ---
with tab3:
    st.title("REDIKSI FEED")
    
    def get_time_of_day_emoji(dt):
        if pd.isna(dt): return ""
        h = dt.hour
        if 5 <= h < 10: return "🌅 Aamusali"
        if 10 <= h < 16: return "☀️ Päiväreeni"
        if 16 <= h < 22: return "🌆 Iltajumppa"
        return "🌚 Yövuoro"

    if not df_log.empty:
        merged = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
        
        for _, row in merged.head(20).iterrows():
            # Data parsing
            timestamp = row['pvm_dt']
            time_str = timestamp.strftime("%d.%m. klo %H:%M") if not pd.isna(timestamp) else row['pvm']
            tod_badge = get_time_of_day_emoji(timestamp)
            gym_info = row['kommentti'].split('@')[-1].strip() if '@' in str(row['kommentti']) else "Sali tuntematon"
            mood_info = row['kommentti'].split('@')[0].strip() if '@' in str(row['kommentti']) else row['kommentti']
            
            st.markdown(f"""
            <div class='feed-item'>
                <div style='display:flex; justify-content:space-between;'>
                    <span class='feed-time'>{time_str} • {tod_badge}</span>
                    <span style='color:#FF4B4B; font-weight:bold;'>{row['nimi'].upper()}</span>
                </div>
                <div style='margin-top:5px; color:#aaa; font-size:14px;'>📍 {gym_info}</div>
                <div class='feed-result'>
                    {row['paino']} kg <span style='color:#666; font-size:16px;'>x</span> {int(row['toistot'])} 
                    <span style='float:right; color:#FF4B4B; font-size:16px; border:1px solid #FF4B4B; padding:2px 8px; border-radius:4px;'>1RM: {row['laskettu_ykkonen']:.1f}</span>
                </div>
                <div style='margin-top:10px; font-style:italic; color:#ddd;'>"{mood_info}"</div>
            </div>
            """, unsafe_allow_html=True)

# --- TAB 4: MINÄ (FINAL POLISH) ---
with tab4:
    import random
    user_name = st.session_state.user['nimi'].title()
    user_email = st.session_state.user['email']
    
    user_history = df_log[df_log['email'] == user_email].sort_values('pvm_dt', ascending=False)
    
    st.markdown(f"### Tervehdys, {user_name} 👋")

    if not user_history.empty:
        last_workout = user_history.iloc[0]
        prev_weight = last_workout['paino']
        prev_reps = int(last_workout['toistot'])
        prev_1rm = last_workout['laskettu_ykkonen']
        prev_date = last_workout['pvm']
        total_sessions = len(user_history)
        
        # KORJATTU "0.0 KG" BUGI: Näytetään vain jos 1rm on järkevä
        target_text = f"Yli {prev_1rm:.1f} kg" if prev_1rm > 0 else "Uusi ennätys"

        st.markdown(f"""
        <div style='background-color: #1a1a1a; padding: 18px; border-radius: 12px; border-left: 5px solid #FF4B4B; margin-bottom: 25px;'>
            <p style='margin:0; font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1px;'>Edellinen suoritus: <b>{prev_date}</b></p>
            <p style='margin:10px 0; font-size: 17px; color: #eee; line-height: 1.4;'>
                Viimeksi kirjasit <b>{prev_weight} kg × {prev_reps}</b>. 
                Tänään on sinun <b>{total_sessions + 1}.</b> kerta tankojen välissä. 
            </p>
            <p style='margin:0; font-size: 14px; color: #FF4B4B; font-weight: bold;'>
                Tavoite tälle päivälle: {target_text} (1RM ennuste)
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background-color: #1a1a1a; padding: 25px; border-radius: 12px; border: 1px dashed #444; text-align: center; margin-bottom: 25px;'>
            <h4 style='margin:10px 0; color: #eee;'>Tee historiaa, {user_name}!</h4>
            <p style='margin:0; font-size: 15px; color: #888;'>Aloita matkasi tänään.</p>
        </div>
        """, unsafe_allow_html=True)

    # LASKENTAKAAVAN TOOLTIP
    with st.expander("ℹ️ Miten 1RM lasketaan? (Brzycki vs. Kalanen)"):
        st.markdown("""
        Tämä palvelu käyttää **Brzyckin kaavaa**:
        $$1RM = \\frac{Paino}{1.0278 - (0.0278 \\times Toistot)}$$
        
        **Miksi?** * **Kalanen.fi** ja monet muut käyttävät usein *Epleyn kaavaa* ($w \\times (1 + r/30)$).
        * Brzycki on yleisesti pidetty hieman tarkempana **penkkipunnerruksessa** ja lyhyemmissä sarjoissa (< 10 toistoa).
        * Epley saattaa antaa hieman liian optimistisia tuloksia (esim. 1 toiston sarjalle se antaa 3.3% bonuksen, meillä 1 toisto on tasan paino).
        """)

    # SYÖTTÖLOMAKE
    if 'w_val' not in st.session_state: st.session_state.w_val = 100.0
    if 'r_val' not in st.session_state: st.session_state.r_val = 1
    if 'mood' not in st.session_state: st.session_state.mood = "✅ Perus"

    st.markdown("---")

    # 1. PAINO
    st.markdown("#### 1. VALITSE PAINO (kg)")
    weight_options = list(range(90, 161, 5))
    w_cols = st.columns(4)
    for i, w in enumerate(weight_options):
        is_selected = st.session_state.w_val == float(w)
        prefix = "⚪ " if w < 110 else "🟡 " if w < 130 else "🟠 " if w < 150 else "🔴 "
        label = f"🎯 {w}" if is_selected else f"{prefix}{w}"
        btn_type = "primary" if is_selected else "secondary"
        if w_cols[i % 4].button(label, key=f"w_{w}", type=btn_type, use_container_width=True):
            st.session_state.w_val = float(w)
            st.rerun()

    # 2. TOISTOT
    st.markdown("---")
    st.markdown("#### 2. MONTAKO TOISTOA?")
    def get_rep_emoji(r):
        if r == 1: return "👑"
        if r <= 3: return "⚡"
        if r <= 6: return "🦾"
        if r <= 9: return "🥵"
        return "💩"

    r_cols = st.columns(5)
    for r in range(1, 21):
        is_selected = st.session_state.r_val == r
        emoji = get_rep_emoji(r)
        label = f"📍 {r}" if is_selected else f"{emoji} {r}"
        btn_type = "primary" if is_selected else "secondary"
        if r_cols[(r-1) % 5].button(label, key=f"r_{r}", type=btn_type, use_container_width=True):
            st.session_state.r_val = r
            st.rerun()

    # 3. YHTEENVETO
    st.markdown("---")
    w_final = st.session_state.w_val
    r_final = st.session_state.r_val
    calculated_1rm = w_final if r_final == 1 else round(w_final / (1.0278 - 0.0278 * r_final), 2)

    st.markdown(f"""
    <div style='background-color: #111; padding: 20px; border-radius: 15px; border: 1px solid #FF4B4B; text-align: center;'>
        <h2 style='margin:0; color:white;'>{w_final} kg × {r_final} toistoa</h2>
        <h1 style='margin:0; color:#FF4B4B;'>{calculated_1rm} kg <small style='font-size:15px; color:#888;'>1RM Ennuste</small></h1>
    </div>
    """, unsafe_allow_html=True)

    # 4. TALLENNUS
    st.write("")
    f_col1, f_col2 = st.columns(2)
    if f_col1.button("🔥 YEAH BUDDY!", use_container_width=True): st.session_state.mood = "YEAH BUDDY!"
    if f_col2.button("🧊 PIENTÄ JUMPPAA", use_container_width=True): st.session_state.mood = "Lähinnä tämmöstä pientä jumppailua (Niilo22)"
    
    gym = st.text_input("📍 Sali", value="Keskus-Sali")

    if st.button("TALLENNA SUORITUS 🏆", type="primary", use_container_width=True):
        payload = {
            "pvm": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "email": st.session_state.user['email'],
            "paino": float(w_final),
            "toistot": int(r_final),
            "laskettu_ykkonen": calculated_1rm,
            "kommentti": f"{st.session_state.mood} @ {gym}"
        }
        loading_msgs = ["Varmistaja hakee magnesiumia...", "Lasketaan raudan tiheyttä...", "Soitetaan Ronnie Colemanille...", "Google Sheets lämmittelee...", "Palvelin vetää vyötä kireämmälle..."]
        chosen_msg = random.choice(loading_msgs)

        with st.spinner(f"⏳ {chosen_msg}"):
            try:
                requests.post(SCRIPT_URL, json=payload, timeout=30)
                st.balloons()
                st.success(f"SUORITUS HYVÄKSYTTY! ({calculated_1rm} kg)")
                time.sleep(2)
                st.rerun()
            except requests.exceptions.Timeout:
                st.warning("⚠️ Hidas yhteys, mutta tulos on todennäköisesti perillä.")
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f"Virhe: {e}")

    st.write("")
    if st.button("Kirjaudu ulos", key="logout_btn"):
        st.session_state.clear()
        st.rerun()
