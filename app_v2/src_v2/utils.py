import streamlit as st
import pandas as pd
from pathlib import Path

#PFADE
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data_v2"
IMAGES_DIR = DATA_DIR / "images_v2"
DATA_FULL_PATH = DATA_DIR / "data_full_v2.xlsx"
EVIDENCE_PATH = DATA_DIR / "data_evidence_v2.xlsx"

#HILFSFUNKTIONEN
def norm(text) -> str:
    return str(text).strip().lower()

def split_semicolon(text) -> list:
    parts = str(text).split(";")
    clean = []
    for p in parts:
        p = p.strip()
        if p != "":
            clean.append(p)
    return clean

def find_image_for_pzn(pzn):
    pzn = str(pzn)
    pzn = "".join(ch for ch in pzn if ch.isdigit()).zfill(8)
    matches = list(IMAGES_DIR.glob(f"{pzn}.*"))
    if len(matches) > 0:
        return matches[0]
    return None

def recom_block(text: str, recom: str):
    r = norm(recom)
    if "nicht" in r:
        border = "#e53935"
    elif r.startswith("sollten"):
        border = "#4caf50"
    elif r.startswith("sollen"):
        border = "#1565c0"
    elif r.startswith("können"):
        border = "#f0a500"
    else:
        border = "#9e9e9e"
    st.markdown(
        f'<div style="'
        f'border-top:1px solid rgba(128,128,128,0.3); '
        f'border-right:1px solid rgba(128,128,128,0.3); '
        f'border-bottom:1px solid rgba(128,128,128,0.3); '
        f'border-left:4px solid {border}; '
        f'background-color:rgba(128,128,128,0.07); '
        f'padding:10px 14px; border-radius:4px; margin:6px 0">{text}</div>',
        unsafe_allow_html=True
    )

#DATEN LADEN
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FULL_PATH, dtype={"pzn": str})
    df.columns = [norm(c) for c in df.columns]
    df["pzn"] = (df["pzn"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8))
    if "plant" in df.columns:
        df["plant"] = df["plant"].fillna("").apply(norm)

    ind_lists = []
    drug_lists = []
    for _, row in df.iterrows():
        inds = split_semicolon(row.get("indication", ""))
        ind_lists.append([norm(i) for i in inds])
        drugs = split_semicolon(row.get("drug", ""))
        drug_lists.append([norm(d) for d in drugs])

    df["ind_list"] = ind_lists
    df["drug_list"] = drug_lists
    return df

@st.cache_data
def load_evidence():
    ev = pd.read_excel(EVIDENCE_PATH)
    ev.columns = [norm(c) for c in ev.columns]

    rows = []
    for _, r in ev.iterrows():
        ind_keys = split_semicolon(r.get("ind", ""))
        drug_keys = split_semicolon(r.get("drug", ""))
        for ind in ind_keys:
            for key in drug_keys:
                new_row = dict(r)
                new_row["ind_key"] = norm(ind)
                new_row["drug_key"] = norm(key)
                new_row["drug_display"] = key.strip()
                rows.append(new_row)

    return pd.DataFrame(rows)

#DETAILANSICHT
def show_details(row: pd.Series, ev_df: pd.DataFrame):
    st.divider()
    st.header(row["handelsname"])

    col1, _, col3 = st.columns([3, 1, 2])

    with col1:
        tab_info, tab_guideline = st.tabs(["Details", "Leitlinie"])

        with tab_info:
            st.subheader(":material/info: Infos")
            st.write(f"Indikation: {row['indication']}")
            st.write(f"Wirkstoff(e): {row['drug']}")
            st.write(f"Darreichungsform: {row['drf']}")
            st.divider()

            st.subheader(":material/pill: Dosierung und Anwendung")
            st.write(f"Anwendung: {row['use']}")
            st.write(f"Einzeldosis: {row['ed']}")
            st.write(f"Tagesmaximaldosis: {row['td']}")

            hinweise = row.get("hinweise", "")
            if isinstance(hinweise, str) and hinweise.strip() != "":
                st.write(f"Weitere Hinweise: {row['hinweise']}")
            st.divider()

            st.subheader(":material/error: Grenzen der Selbstmedikation")
            st.warning(f"Anwendungsdauer ohne ärztliche Rücksprache: {row['grenzen']}")
            st.divider()

            st.subheader(":material/document_search: Quelle")
            st.write(f"{row['source']}")

        with tab_guideline:
            with st.expander("Legende Empfehlungsgrad"):
                st.markdown(
                    '<div style="border-left:4px solid #1565c0; padding:3px 8px; margin:3px 0; font-size:0.85em">Starke Empfehlung (sollen)</div>'
                    '<div style="border-left:4px solid #4caf50; padding:3px 8px; margin:3px 0; font-size:0.85em">Empfehlung (sollten)</div>'
                    '<div style="border-left:4px solid #f0a500; padding:3px 8px; margin:3px 0; font-size:0.85em">Empfehlung offen (können)</div>'
                    '<div style="border-left:4px solid #e53935; padding:3px 8px; margin:3px 0; font-size:0.85em">Nicht empfohlen</div>',
                    unsafe_allow_html=True
                )

            ind_list = row["ind_list"]
            drug_list = row["drug_list"]

            ev_ind_rows = []
            for _, erow in ev_df.iterrows():
                if erow["ind_key"] in ind_list:
                    ev_ind_rows.append(erow)

            if len(ev_ind_rows) == 0:
                st.info("Keine Leitlinie zur Indikation gefunden.")
            else:
                ev_ind = pd.DataFrame(ev_ind_rows)

                hits_rows = []
                for drug in drug_list:
                    for _, erow in ev_ind.iterrows():
                        key = erow["drug_key"]
                        if key != "" and key in drug:
                            hits_rows.append(erow)

                if len(hits_rows) == 0:
                    st.info("Die Wirkstoffe dieses Präparats werden nicht in der Leitlinie genannt.")
                else:
                    hits_df = pd.DataFrame(hits_rows).drop_duplicates()

                    groups = {}
                    for _, r in hits_df.iterrows():
                        group_key = (r.get("ind_key"), r.get("ws_gruppe"), r.get("recom"), r.get("source"), r.get("stand"))
                        display = r.get("drug_display", r.get("drug_key", ""))
                        if group_key not in groups:
                            groups[group_key] = set()
                        groups[group_key].add(display)

                    output_rows = []
                    for group_key, displays in groups.items():
                        ind_key, ws_gruppe, recom, source, stand = group_key
                        drug_list_text = ", ".join(sorted(displays))
                        output_rows.append((ind_key, ws_gruppe, recom, source, stand, drug_list_text))

                    output_rows.sort(key=lambda x: (str(x[0]), str(x[1])))

                    current_ind = None
                    for (ind_key, ws_gruppe, recom, source, stand, drug_list_text) in output_rows:
                        if ind_key != current_ind:
                            if current_ind is not None:
                                st.markdown("&nbsp;", unsafe_allow_html=True)
                            st.markdown(f"**Bei {ind_key.title()}:**")
                            current_ind = ind_key
                        recom_block(
                            f"{ws_gruppe} ({drug_list_text}) {recom}"
                            f"<br><span style='font-size:0.85em; opacity:0.7'>Quelle: {source} · Stand: {stand}</span>",
                            recom
                        )

    with col3:
        img_path = find_image_for_pzn(row["pzn"])
        if img_path:
            st.image(str(img_path), width="content", caption=f"Copyright: {row['image_cr']}")

#SEITENLOGIK
def run_page(titel: str, kategorie_inds: set, page_key: str):
    df = load_data()
    ev_df = load_evidence()

    #auf diese kategorie vorfiltern
    keep = []
    for _, row in df.iterrows():
        keep.append(any(i in kategorie_inds for i in row["ind_list"]))
    df_kat = df[keep]

    st.title(f"Beratungshilfe: Selbstmedikation bei {titel}")

    with st.expander("Disclaimer"):
        st.write('''Die Auswahl der dargestellten Fertigarzneimittel dient der Orientierung über in der Selbstmedikation
        bei Erkältungssymptomen sowie Magen-Darm-Erkrankungen verfügbaren Präparate und stellt weder eine Abgabeempfehlung noch eine Bewertung oder Bevorzugung einzelner Fertigarzneimittel dar.''')
        st.write('''Diese Beratungshilfe wird ausschließlich zu Lehr- und Übungszwecken im Rahmen des Praktikums "Übungsapotheke" im
        Studiengang Pharmazie an der Universität Leipzig eingesetzt.''')
        st.write('''Die enthaltenen Informationen basieren unter anderem auf Angaben aus Fachinformationen und sind ausschließlich für pharmazeutisches Fachpersonal bestimmt.
        Eine Weitergabe oder Anwendung der Inhalte außerhalb des genannten Lehrkontextes ist nicht vorgesehen.''')

    st.info(":material/lightbulb: Nutze die Filter in der Seitenleiste, um passende Präparate zu finden. "
            "Klicke anschließend eine Zeile an, um die Informationen zum Präparat anzuzeigen.")

    #SIDEBAR FILTER
    st.sidebar.header("Filter")

    all_inds = sorted(set(i for inds in df_kat["ind_list"] for i in inds))
    pretty_to_norm = {i.title(): i for i in all_inds}
    ind_options_pretty = sorted(pretty_to_norm.keys())

    indikationen_filter_pretty = st.sidebar.multiselect(
        "Nach Indikationen filtern",
        options=ind_options_pretty,
        default=[],
        key=f"ind_filter_{page_key}"
    )
    indikationen_filter = [pretty_to_norm[p] for p in indikationen_filter_pretty]

    df_ind = df_kat.copy()
    if indikationen_filter:
        selected = set(indikationen_filter)
        df_ind = df_ind[df_ind["ind_list"].apply(lambda inds: any(i in selected for i in inds))]

    ls_drf = sorted(df_ind["drf"].dropna().unique().tolist())

    prev = st.session_state.get(f"drf_filter_{page_key}", [])
    prev_valid = [x for x in prev if x in ls_drf]

    darreichung_filter = st.sidebar.multiselect(
        "Nach Darreichungsformen filtern",
        options=ls_drf,
        default=prev_valid,
        key=f"drf_filter_{page_key}"
    )

    pflanzenwahl = st.sidebar.selectbox(
        "Nach pflanzlich/nicht pflanzlich filtern",
        options=["keine Auswahl", "Pflanzlich", "Nicht Pflanzlich"],
        index=0,
        key=f"pflanz_{page_key}"
    )

    st.sidebar.divider()
    suchtext = st.sidebar.text_input("Freitextsuche (Präparat oder Wirkstoff)", key=f"suche_{page_key}")

    if st.sidebar.button("Daten neu laden", key=f"reload_{page_key}"):
        st.cache_data.clear()
        st.rerun()

    #FILTER ANWENDEN
    filtered = df_ind.copy()

    if darreichung_filter:
        filtered = filtered[filtered["drf"].isin(darreichung_filter)]

    if pflanzenwahl == "Pflanzlich":
        filtered = filtered[filtered["plant"] == "ja"]
    elif pflanzenwahl == "Nicht Pflanzlich":
        filtered = filtered[filtered["plant"] == "nein"]

    q = norm(suchtext)
    if q:
        filtered = filtered[
            filtered["handelsname"].apply(norm).str.contains(q) |
            filtered["drug"].apply(norm).str.contains(q)
        ]

    st.caption(f"Gefundene Präparate: {len(filtered)}")

    if len(filtered) == 0:
        st.info("Keine Präparate mit diesen Kriterien gefunden.")
        st.stop()

    #HAUPTBEREICH
    st.subheader("Präparateübersicht")

    display_df = filtered[["handelsname", "indication", "drug", "drf"]].rename(columns={
        "handelsname": "Name Fertigarzneimittel/Präparat",
        "indication": "Indikation",
        "drug": "Wirkstoff(e)",
        "drf": "Darreichungsform",
    })

    event = st.dataframe(
        display_df,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True,
    )

    selected_rows = event.selection.rows
    if selected_rows:
        row = filtered.iloc[selected_rows[0]]
        show_details(row, ev_df)
    else:
        st.caption("Zeile anklicken, um die Details zum Präparat anzuzeigen.")

    st.divider()
    st.caption('''© 2025 · Tanjana Harings · Lehrtool für das Praktikum „Übungsapotheke"''')

    with st.expander("Über diese App"):
        st.caption('''Diese webbasierte Beratungshilfe wurde als Lehr- und Übungstool für das Praktikum "Übungsapotheke" im Studiengang Pharmazie an der Universität Leipzig entwickelt.''')
        st.caption('''Konzeption und Umsetzung: Nele Sebök, Tanjana Harings''')
        st.caption('''Kontakt: Tanjana Harings, Apothekerin, Wissenschaftliche Mitarbeiterin, Klinische Pharmazie, Institut für Pharmazie, Medizinische Fakultät, Universität Leipzig, tanjana.harings@uni-leipzig.de''')
