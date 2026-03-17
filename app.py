import pandas as pd
import streamlit as st
from data import (
    get_odp_data,
    get_avanzamenti_data,
    get_odp_from_sql,
    get_avanzamenti_from_sql
)
from transform import prepara_avanzamenti, unisci_dati
from auth import require_login, get_current_role, get_current_user, logout_button

st.set_page_config(
    page_title="Dashboard Cella Robotica Tecnorobot",
    layout="wide",
    page_icon="🤖"
)

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
require_login()

utente = get_current_user()
ruolo = get_current_role()

# -------------------------------------------------
# CARICAMENTO DATI
# -------------------------------------------------
df_odp_sql = get_odp_from_sql()
df_av_sql = get_avanzamenti_from_sql()

df_odp = df_odp_sql if df_odp_sql is not None else get_odp_data()
df_av_raw = df_av_sql if df_av_sql is not None else get_avanzamenti_data()

df_av = prepara_avanzamenti(df_av_raw)
df_merge = unisci_dati(df_odp, df_av)

# -------------------------------------------------
# PROTEZIONI COLONNE
# -------------------------------------------------
if "ULTIMO_AGGIORNAMENTO" not in df_av.columns:
    if "timestamp_evento" in df_av.columns:
        df_av["ULTIMO_AGGIORNAMENTO"] = df_av["timestamp_evento"]
    else:
        df_av["ULTIMO_AGGIORNAMENTO"] = pd.NaT

if "TEMPO_INIZIO" not in df_av.columns:
    df_av["TEMPO_INIZIO"] = pd.NaT

if "TEMPO_FINE" not in df_av.columns:
    df_av["TEMPO_FINE"] = pd.NaT

# -------------------------------------------------
# KPI
# -------------------------------------------------
pezzi_prodotti_tot = int(df_av["QTA_PRODOTTA"].fillna(0).sum()) if "QTA_PRODOTTA" in df_av.columns else 0
tempo_medio_ciclo = round(df_av["TEMPO_ESECUZ"].fillna(0).mean(), 1) if "TEMPO_ESECUZ" in df_av.columns and len(df_av) > 0 else 0
allarmi_attivi = int((df_av["TIPO_RECORD"] == "Diagnostica").sum()) if "TIPO_RECORD" in df_av.columns else 0
commesse_attive = int((df_av["FLAG_FINITO"] == 1).sum()) if "FLAG_FINITO" in df_av.columns else 0
commesse_terminate = int(df_av["FLAG_FINITO"].isin([199, 299]).sum()) if "FLAG_FINITO" in df_av.columns else 0

if allarmi_attivi > 0:
    stato_macchina = "🔴 Con allarme attivo"
elif commesse_attive > 0:
    stato_macchina = "🟢 In produzione"
else:
    stato_macchina = "🟡 In attesa"

ultimo_record = None
if "timestamp_evento" in df_av.columns and not df_av["timestamp_evento"].isna().all():
    ultimo_record = df_av["timestamp_evento"].max()

# -------------------------------------------------
# PAGINE DISPONIBILI IN BASE AL RUOLO
# -------------------------------------------------
if ruolo == "Operatore":
    pagine_disponibili = ["Dashboard", "Ordini ODP", "Avanzamenti"]
elif ruolo == "Responsabile":
    pagine_disponibili = ["Dashboard", "Ordini ODP", "Avanzamenti", "Diagnostica"]
else:
    pagine_disponibili = ["Dashboard", "Ordini ODP", "Avanzamenti", "Diagnostica"]

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("Navigazione")
pagina = st.sidebar.radio("Seleziona sezione", pagine_disponibili)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Utente:** {utente}")
st.sidebar.markdown(f"**Ruolo:** {ruolo}")
st.sidebar.markdown("**Sistema:** Tecnorobot")
st.sidebar.markdown("**Database atteso:** ROBOT_E12345")

if df_odp_sql is not None and df_av_sql is not None:
    st.sidebar.success("Fonte dati: SQL Server")
else:
    st.sidebar.warning("Fonte dati: simulazione locale")

st.sidebar.markdown(f"**Stato macchina:** {stato_macchina}")

if ultimo_record is not None:
    st.sidebar.markdown(f"**Ultimo aggiornamento:** {ultimo_record}")

logout_button()

# -------------------------------------------------
# PAGINA DASHBOARD
# -------------------------------------------------
if pagina == "Dashboard":
    st.title("Dashboard Cella Robotica di Saldatura - Tecnorobot")
    st.markdown("Monitoraggio ordini, avanzamenti, stato macchina e diagnostica")

    st.subheader("Stato cella robotica")
    if stato_macchina.startswith("🔴"):
        st.error(stato_macchina)
    elif stato_macchina.startswith("🟡"):
        st.warning(stato_macchina)
    else:
        st.success(stato_macchina)

    if ultimo_record is not None:
        st.caption(f"Ultimo aggiornamento sistema: {ultimo_record}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ordini ODP", len(df_odp))
    col2.metric("Pezzi prodotti", pezzi_prodotti_tot)
    col3.metric("Tempo medio ciclo (s)", tempo_medio_ciclo)
    col4.metric("Allarmi attivi", allarmi_attivi)

    col5, col6 = st.columns(2)
    col5.metric("Commesse in lavorazione", commesse_attive)
    col6.metric("Commesse terminate", commesse_terminate)

    st.divider()

    commesse = ["Tutte"] + sorted(df_merge["COMMESSA_ODP"].dropna().astype(str).unique().tolist())
    commessa_sel = st.selectbox("Filtra per commessa", commesse)

    df_view = df_merge.copy()
    if commessa_sel != "Tutte":
        df_view = df_view[df_view["COMMESSA_ODP"].astype(str) == commessa_sel]

    st.subheader("Vista unificata Ordini + Avanzamenti")
    vista = df_view[[
        "ID",
        "PROGRAMMA_ODP",
        "COMMESSA_ODP",
        "DES_PROD",
        "ARTICOLO_ODP",
        "QUANT_DA_PRODURRE",
        "QTA_PRODOTTA",
        "SCOSTAMENTO_QTA",
        "STAZIONE",
        "TEMPO_INIZIO",
        "TEMPO_FINE",
        "TEMPO_ESECUZ",
        "STATO_COMMESSA",
        "TIPO_RECORD"
    ]].rename(columns={
        "PROGRAMMA_ODP": "Programma robot",
        "COMMESSA_ODP": "Commessa",
        "DES_PROD": "Descrizione pezzo",
        "ARTICOLO_ODP": "Codice articolo",
        "QUANT_DA_PRODURRE": "Quantità da produrre",
        "QTA_PRODOTTA": "Quantità prodotta",
        "SCOSTAMENTO_QTA": "Scostamento",
        "STAZIONE": "Stazione",
        "TEMPO_INIZIO": "Inizio lavorazione",
        "TEMPO_FINE": "Fine lavorazione",
        "TEMPO_ESECUZ": "Tempo ciclo (s)",
        "STATO_COMMESSA": "Stato",
        "TIPO_RECORD": "Tipo record"
    })

    st.dataframe(vista, use_container_width=True)

    st.subheader("Confronto quantità da produrre vs quantità prodotta")
    chart_df = df_view[[
        "COMMESSA_ODP",
        "QUANT_DA_PRODURRE",
        "QTA_PRODOTTA"
    ]].copy()

    chart_df["QTA_PRODOTTA"] = chart_df["QTA_PRODOTTA"].fillna(0)
    chart_df = chart_df.set_index("COMMESSA_ODP")
    st.bar_chart(chart_df)

    st.subheader("Commesse in lavorazione")
    df_attive = df_av[df_av["FLAG_FINITO"] == 1].copy() if "FLAG_FINITO" in df_av.columns else pd.DataFrame()

    if "ULTIMO_AGGIORNAMENTO" not in df_attive.columns:
        df_attive["ULTIMO_AGGIORNAMENTO"] = pd.NaT

    if len(df_attive) > 0:
        attive = df_attive[[
            "COMMESSA",
            "ARTICOLO",
            "STAZIONE",
            "TEMPO_INIZIO",
            "ULTIMO_AGGIORNAMENTO",
            "TEMPO_ESECUZ",
            "QTA_PRODOTTA",
            "STATO_COMMESSA"
        ]].rename(columns={
            "COMMESSA": "Commessa",
            "ARTICOLO": "Codice articolo",
            "STAZIONE": "Stazione",
            "TEMPO_INIZIO": "Inizio lavorazione",
            "ULTIMO_AGGIORNAMENTO": "Ultimo aggiornamento",
            "TEMPO_ESECUZ": "Tempo ciclo (s)",
            "QTA_PRODOTTA": "Quantità prodotta",
            "STATO_COMMESSA": "Stato"
        })
        st.dataframe(attive, use_container_width=True)
    else:
        st.write("Nessuna commessa attiva.")

    st.subheader("Commesse concluse")
    df_concluse = df_av[df_av["FLAG_FINITO"].isin([199, 299])].copy() if "FLAG_FINITO" in df_av.columns else pd.DataFrame()

    if len(df_concluse) > 0:
        concluse = df_concluse[[
            "COMMESSA",
            "ARTICOLO",
            "STAZIONE",
            "TEMPO_INIZIO",
            "TEMPO_FINE",
            "TEMPO_ESECUZ",
            "QTA_PRODOTTA",
            "STATO_COMMESSA"
        ]].rename(columns={
            "COMMESSA": "Commessa",
            "ARTICOLO": "Codice articolo",
            "STAZIONE": "Stazione",
            "TEMPO_INIZIO": "Inizio lavorazione",
            "TEMPO_FINE": "Fine lavorazione",
            "TEMPO_ESECUZ": "Tempo ciclo (s)",
            "QTA_PRODOTTA": "Quantità prodotta",
            "STATO_COMMESSA": "Stato"
        })
        st.dataframe(concluse, use_container_width=True)
    else:
        st.write("Nessuna commessa conclusa.")

# -------------------------------------------------
# PAGINA ORDINI ODP
# -------------------------------------------------
elif pagina == "Ordini ODP":
    st.title("Ordini di Produzione (ODP)")
    st.markdown("Visualizzazione degli ordini caricati verso la cella robotica")

    vista_odp = df_odp.rename(columns={
        "ID": "ID",
        "PROGRAMMA": "Programma robot",
        "COMMESSA": "Commessa",
        "DES_PROD": "Descrizione pezzo",
        "ARTICOLO": "Codice articolo",
        "QUANT_DA_PRODURRE": "Quantità da produrre"
    })

    st.dataframe(vista_odp, use_container_width=True)

# -------------------------------------------------
# PAGINA AVANZAMENTI
# -------------------------------------------------
elif pagina == "Avanzamenti":
    st.title("Avanzamenti Produzione Robot")
    st.markdown("Monitoraggio dei record di produzione restituiti dalla cella")

    df_prod = df_av[df_av["TIPO_RECORD"] == "Produzione"].copy() if "TIPO_RECORD" in df_av.columns else pd.DataFrame()

    if len(df_prod) > 0:
        avanz = df_prod[[
            "COMMESSA",
            "ARTICOLO",
            "STAZIONE",
            "TEMPO_INIZIO",
            "TEMPO_FINE",
            "ULTIMO_AGGIORNAMENTO",
            "TEMPO_ESECUZ",
            "QTA_PRODOTTA",
            "STATO_COMMESSA"
        ]].rename(columns={
            "COMMESSA": "Commessa",
            "ARTICOLO": "Codice articolo",
            "STAZIONE": "Stazione",
            "TEMPO_INIZIO": "Inizio lavorazione",
            "TEMPO_FINE": "Fine lavorazione",
            "ULTIMO_AGGIORNAMENTO": "Ultimo aggiornamento",
            "TEMPO_ESECUZ": "Tempo ciclo (s)",
            "QTA_PRODOTTA": "Quantità prodotta",
            "STATO_COMMESSA": "Stato"
        })

        st.dataframe(avanz, use_container_width=True)
    else:
        st.write("Nessun avanzamento disponibile.")

# -------------------------------------------------
# PAGINA DIAGNOSTICA
# -------------------------------------------------
elif pagina == "Diagnostica":
    st.title("Diagnostica e Allarmi")
    st.markdown("Segnalazioni diagnostiche e anomalie di lavorazione")

    if ruolo == "Operatore":
        st.warning("Questa sezione non è disponibile per il ruolo Operatore.")
    else:
        df_diag = df_av[df_av["TIPO_RECORD"] == "Diagnostica"].copy() if "TIPO_RECORD" in df_av.columns else pd.DataFrame()

        if len(df_diag) > 0:
            st.dataframe(df_diag, use_container_width=True)
        else:
            st.success("Nessun allarme presente.")
