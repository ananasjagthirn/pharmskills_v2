import streamlit as st

#befehl für terminal um app lokal zu starten: streamlit run app_v2/src_v2/app_v2.py

st.set_page_config(page_title="Übungsapotheke", layout="wide")

pg = st.navigation([
    st.Page("pages/alle.py", title="Alle Präparate", icon=":material/medication:"),
    st.Page("pages/erkaeltung.py", title="Erkältungssymptome", icon=":material/sick:"),
    st.Page("pages/magen_darm.py", title="Magen-Darm-Erkrankungen", icon=":material/gastroenterology:"),
])
pg.run()
