import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Übungsapotheke – Erkältung",
    layout="wide"
)

# ---------- Daten laden ----------
@st.cache_data
def load_data():
    # Dateiname ggf. anpassen
    df = pd.read_excel("data_example.xlsx")
    return df

df = load_data()

st.title("Beratungshilfe: Selbstmedikation bei Erkältung")

st.markdown(
    "Nutze die Filter in der Seitenleiste, um passende Präparate zu finden, "
    "und wähle anschließend ein Präparat aus, um Details für das Beratungsgespräch zu sehen."
)

# ---------- Sidebar: Modus & Filter ----------
st.sidebar.header("Suchmodus & Filter")

modus = st.sidebar.radio(
    "Modus wählen",
    ("Nach Präparat suchen", "Nach Indikation stöbern")
)

# dynamische Listen aus den Daten
indikationen = sorted(df["indikation"].dropna().unique())
darreichungen = sorted(df["darreichungsform"].dropna().unique())

indikation_filter = st.sidebar.multiselect(
    "Indikation filtern",
    options=indikationen,
    default=[]
)

darreichung_filter = st.sidebar.multiselect(
    "Darreichungsform filtern",
    options=darreichungen,
    default=[]
)

suchtext = st.sidebar.text_input("Freitext (Präparat oder Wirkstoff)")

# ---------- Filter anwenden ----------
filtered = df.copy()

if indikation_filter:
    filtered = filtered[filtered["indikation"].isin(indikation_filter)]

if darreichung_filter:
    filtered = filtered[filtered["darreichungsform"].isin(darreichung_filter)]

if suchtext:
    mask = (
        filtered["praeparat_name"].str.contains(suchtext, case=False, na=False)
        | filtered["wirkstoff"].str.contains(suchtext, case=False, na=False)
    )
    filtered = filtered[mask]

st.write(f"Gefundene Präparate: **{len(filtered)}**")

if len(filtered) == 0:
    st.info("Keine Präparate mit diesen Kriterien gefunden.")
    st.stop()

# ---------- Hilfsfunktion: Detailansicht ----------
def show_details(row: pd.Series):
    st.markdown("---")
    st.subheader(row["praeparat_name"])
    st.write(f"**Indikation:** {row['indikation']}")
    st.write(f"**Wirkstoff(e):** {row['wirkstoff']}")
    st.write(f"**Darreichungsform:** {row['darreichungsform']}")

    st.markdown("### Dosierung")
    st.write(row["dosierung"])

    st.markdown("### Anwendung")
    st.write(row["anwendung"])

    st.markdown("### Hinweise")
    st.write(row["hinweise"])

# ---------- Hauptbereich ----------
if modus == "Nach Präparat suchen":
    st.subheader("Präparateübersicht")

    st.dataframe(
        filtered[["praeparat_name", "indikation", "wirkstoff", "darreichungsform"]]
    )

    auswahl = st.selectbox(
        "Präparat auswählen:",
        options=filtered["praeparat_name"].unique()
    )

    if auswahl:
        row = filtered[filtered["praeparat_name"] == auswahl].iloc[0]
        show_details(row)

else:  # "Nach Indikation stöbern"
    st.subheader("Nach Indikation stöbern")

    ind = st.selectbox(
        "Indikation auswählen:",
        options=indikationen
    )

    ind_df = filtered[filtered["indikation"] == ind]

    st.markdown(f"### Präparate für: *{ind}*")
    st.dataframe(
        ind_df[["praeparat_name", "wirkstoff", "darreichungsform"]]
    )

    auswahl = st.selectbox(
        "Präparat auswählen:",
        options=ind_df["praeparat_name"].unique(),
        key="auswahl_indikation"
    )

    if auswahl:
        row = ind_df[ind_df["praeparat_name"] == auswahl].iloc[0]
        show_details(row)