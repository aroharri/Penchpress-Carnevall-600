# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="DIAGNOSTICS", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

st.write("### 🔍 Yhteyden diagnostiikka")

# 1. Testataan URL
try:
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    st.success(f"URL löytyi Secretsistä")
except:
    st.error("URL puuttuu Secrets-osiosta!")
    st.stop()

# 2. Testataan välilehdet yksitellen
for sheet in ["users", "logi", "settings"]:
    try:
        test_df = conn.read(worksheet=sheet, ttl=0)
        st.success(f"Välilehti '{sheet}' OK! (Löytyi {len(test_df)} riviä)")
    except Exception as e:
        st.warning(f"Välilehti '{sheet}' EI TOIMI. Virhe: {e}")

st.info("Jos kaikki välilehdet antavat virheen, vika on URL-linkissä tai jakoasetuksissa.")
