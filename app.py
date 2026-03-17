import pandas as pd
import streamlit as st
import base64
from pathlib import Path

from auth import require_login, get_current_role, get_current_user, logout_button
from data import get_orders_data, get_orders_from_sql
from transform import (
    prepare_orders,
    get_machine_status,
    get_orders_for_display,
    build_orders_table,
    style_rows_by_status,
    set_priority,
    set_order_in_work,
    complete_current_order_demo,
    apply_fifo_sequence,
    apply_manual_sequence
)
from notifications import send_completion_email, DEFAULT_ADMIN_EMAIL

st.set_page_config(
    page_title="Dashboard Cella Robotica Tecnorobot",
    layout="wide",
    page_icon="🤖"
)

# -------------------------------------------------
# BACKGROUND
# -------------------------------------------------
def set_background(png_file: str) -> None:
    file_path = Path(png_file)
    if not file_path.exists():
        st.error(f"Immagine non trovata: {png_file}")
        return

    encoded = base64.b64encode(file_path.read_bytes()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                linear-gradient(rgba(8,25,45,0.28), rgba(8,25,45,0.28)),
                url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("background.png")

# -------------------------------------------------
# STILE GLOBALE
# -------------------------------------------------
st.markdown("""
<style>

/* FONT E SPAZIATURA */
html, body, [class*="css"] {
    font-family: "Inter", sans-serif;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

/* TITOLI PRINCIPALI */
h1, h2, h3 {
    color: white !important;
}

/* TESTI GENERALI */
p, label, .stMarkdown, .stCaption {
    color: #D8E2EB !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: rgba(10,20,35,0.88);
}

/* CARD METRICHE STANDARD STREAMLIT */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 12px;
    padding: 10px;
    backdrop-filter: blur(4px);
}

/* DATAFRAME */
div[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.92);
    border-radius: 12px;
    padding: 4px;
}

/* CARD CUSTOM */
.soft-card {
    background: rgba(255,255,255,0.94);
    border: 1px solid #e4e8ef;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 12px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
}

.section-title {
    color: #1f2a37 !important;
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.section-sub {
    color: #4b5563 !important;
    font-size: 0.92rem;
    margin-bottom: 0.5rem;
}

/* KPI WOW */
.kpi-card {
    background: rgba(255,255,255,0.92);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
    margin-bottom: 10px;
}

.kpi-title {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

/* BADGE */
.badge-ok {
    background: #dcfce7;
    color: #166534;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.badge-warn {
    background: #fef9c3;
    color: #854d0e;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.badge-alert {
    background: #fee2e2;
    color: #991b1b;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

/* BOTTONI */
button,
button * {
    color: #1f2a37 !important;
    font-weight: 600 !important;
}

button:hover,
button:hover * {
    color: #0f172a !important;
}

/* Evidenzia solo la colonna di editing sequenza */
div[data-testid="stDataEditor"] table td:nth-child(4),
div[data-testid="stDataEditor"] table th:nth-child(4) {
    border: 2px solid #4a90e2 !important;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
require_login()
utente = get_current_user()
ruolo = get_current_role()

# -------------------------------------------------
# INIT SESSION
# -------------------------------------------------
if "orders_df" not in st.session_state:
    df_sql = get_orders_from_sql()
    base_df = df_sql if df_sql is not None else get_orders_data()
    st.session_state.orders_df = prepare_orders(base_df)

if "planning_mode" not in st.session_state:
    st.session_state.planning_mode = "FIFO"

if "admin_email" not in st.session_state:
    st.session_state.admin_email = DEFAULT_ADMIN_EMAIL

if "notification_log" not in st.session_state:
    st.session_state.notification_log = []

# -------------------------------------------------
# LOAD ORDERS
# -------------------------------------------------
orders_df = prepare_orders(st.session_state.orders_df.copy())

if st.session_state.planning_mode == "FIFO":
    orders_df = apply_fifo_sequence(orders_df)
else:
    orders_df = apply_manual_sequence(orders_df)

st.session_state.orders_df = orders_df.copy()

# -------------------------------------------------
# KPI E STATO
# -------------------------------------------------
machine_status = get_machine_status(orders_df)
in_work_count = int((orders_df["STATO_ORDINE"] == "IN_LAVORAZIONE").sum())
completed_count = int((orders_df["STATO_ORDINE"] == "COMPLETATO").sum())
to_do_count = int((orders_df["STATO_ORDINE"] == "DA_LAVORARE").sum())
pieces_done = int(orders_df["QTA_PRODOTTA"].fillna(0).sum())

valid_cycle = orders_df["TEMPO_ESECUZ"].fillna(0).replace(0, pd.NA).dropna()
avg_cycle = round(valid_cycle.mean(), 1) if len(valid_cycle) > 0 else 0

active_order_df = orders_df[orders_df["STATO_ORDINE"] == "IN_LAVORAZIONE"].copy()
completed_orders_df = orders_df[orders_df["STATO_ORDINE"] == "COMPLETATO"].copy()

latest_update = None
if len(active_order_df) > 0:
    latest_update = active_order_df["TEMPO_INIZIO"].max()
elif len(completed_orders_df) > 0:
    latest_update = completed_orders_df["TEMPO_FINE"].max()

# KPI aggiuntivi "wow"
total_planned = max(int(orders_df["QUANT_DA_PRODURRE"].fillna(0).sum()), 1)
oee_est = round(min(100, (pieces_done / total_planned) * 100), 1)
saturazione = 100 if in_work_count > 0 else 0

# -------------------------------------------------
# RUOLI E PAGINE
# -------------------------------------------------
if ruolo == "Operatore":
    pages = ["Dashboard", "Ordini", "Avanzamenti"]
elif ruolo == "Responsabile":
    pages = ["Dashboard", "Ordini", "Avanzamenti", "Diagnostica"]
else:
    pages = ["Dashboard", "Ordini", "Avanzamenti", "Diagnostica", "Pianificazione"]

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("Navigazione")
page = st.sidebar.radio("Seleziona sezione", pages)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Utente:** {utente}")
st.sidebar.markdown(f"**Ruolo:** {ruolo}")
st.sidebar.markdown("**Sistema:** Tecnorobot")
st.sidebar.markdown("**Stazione di lavoro:** 1")
st.sidebar.markdown("**Database atteso:** ROBOT_E12345")
st.sidebar.markdown(f"**Modalità pianificazione:** {st.session_state.planning_mode}")
st.sidebar.markdown(f"**Stato macchina:** {machine_status}")

if latest_update is not None and pd.notna(latest_update):
    st.sidebar.markdown(f"**Ultimo aggiornamento:** {latest_update}")

if len(st.session_state.notification_log) > 0:
    last_note = st.session_state.notification_log[-1]
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Ultima notifica:**")
    st.sidebar.info(last_note)

logout_button()

# -------------------------------------------------
# FUNZIONI SUPPORTO
# -------------------------------------------------
def section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="section-title">{title}</div>
            <div class="section-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def kpi_card(title: str, value):
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

def dataframe_to_csv_bytes(df_source: pd.DataFrame):
    return df_source.to_csv(index=False).encode("utf-8-sig")

def format_dt(value):
    if pd.isna(value):
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")

def styled_orders_dataframe(df_source):
    display_df = get_orders_for_display(df_source, st.session_state.planning_mode)
    display_df = build_orders_table(display_df)

    styler = (
        display_df.style
        .apply(style_rows_by_status, axis=1)
        .format({
            "Inizio lavorazione": format_dt,
            "Fine lavorazione": format_dt
        })
    )
    return display_df, styler

def build_current_order_view(df_source):
    current_df = df_source[df_source["STATO_ORDINE"] == "IN_LAVORAZIONE"].copy()
    if len(current_df) == 0:
        return pd.DataFrame()

    return current_df[[
        "COMMESSA",
        "ARTICOLO",
        "DES_PROD",
        "QUANT_DA_PRODURRE",
        "QTA_PRODOTTA",
        "TEMPO_INIZIO",
        "TEMPO_ESECUZ"
    ]].rename(columns={
        "COMMESSA": "Commessa",
        "ARTICOLO": "Codice articolo",
        "DES_PROD": "Descrizione pezzo",
        "QUANT_DA_PRODURRE": "Quantità da produrre",
        "QTA_PRODOTTA": "Quantità prodotta",
        "TEMPO_INIZIO": "Inizio lavorazione",
        "TEMPO_ESECUZ": "Tempo ciclo (s)"
    })

def build_completed_view(df_source):
    completed_df = df_source[df_source["STATO_ORDINE"] == "COMPLETATO"].copy()
    if len(completed_df) == 0:
        return pd.DataFrame()

    return completed_df[[
        "COMMESSA",
        "ARTICOLO",
        "DES_PROD",
        "QTA_PRODOTTA",
        "TEMPO_INIZIO",
        "TEMPO_FINE",
        "TEMPO_ESECUZ"
    ]].rename(columns={
        "COMMESSA": "Commessa",
        "ARTICOLO": "Codice articolo",
        "DES_PROD": "Descrizione pezzo",
        "QTA_PRODOTTA": "Quantità prodotta",
        "TEMPO_INIZIO": "Inizio lavorazione",
        "TEMPO_FINE": "Fine lavorazione",
        "TEMPO_ESECUZ": "Tempo ciclo (s)"
    })

def build_progress_view(df_source):
    return df_source[[
        "COMMESSA",
        "ARTICOLO",
        "STATO_ORDINE",
        "QTA_PRODOTTA",
        "QUANT_DA_PRODURRE",
        "TEMPO_INIZIO",
        "TEMPO_FINE",
        "TEMPO_ESECUZ"
    ]].rename(columns={
        "COMMESSA": "Commessa",
        "ARTICOLO": "Codice articolo",
        "STATO_ORDINE": "Stato ordine",
        "QTA_PRODOTTA": "Quantità prodotta",
        "QUANT_DA_PRODURRE": "Quantità da produrre",
        "TEMPO_INIZIO": "Inizio lavorazione",
        "TEMPO_FINE": "Fine lavorazione",
        "TEMPO_ESECUZ": "Tempo ciclo (s)"
    })

def build_diagnostic_view(df_source):
    diag_df = df_source[df_source["ALLARME1"].fillna("").astype(str).str.strip() != ""].copy()
    if len(diag_df) == 0:
        return pd.DataFrame()

    return diag_df[[
        "COMMESSA",
        "ARTICOLO",
        "ALLARME1",
        "STATO_ORDINE"
    ]].rename(columns={
        "COMMESSA": "Commessa",
        "ARTICOLO": "Codice articolo",
        "ALLARME1": "Allarme",
        "STATO_ORDINE": "Stato ordine"
    })

def render_download_button(df_source, label, filename):
    st.download_button(
        label,
        data=dataframe_to_csv_bytes(df_source),
        file_name=filename,
        mime="text/csv"
    )

def build_timeline_source(df_source):
    tl = df_source.copy()
    tl["TEMPO_INIZIO"] = pd.to_datetime(tl["TEMPO_INIZIO"], errors="coerce")
    tl["TEMPO_FINE"] = pd.to_datetime(tl["TEMPO_FINE"], errors="coerce")
    tl["EVENTO"] = tl["TEMPO_FINE"].combine_first(tl["TEMPO_INIZIO"])
    tl = tl.sort_values(by="EVENTO", na_position="last")

    timeline_table = tl[[
        "COMMESSA",
        "STATO_ORDINE",
        "QTA_PRODOTTA",
        "TEMPO_INIZIO",
        "TEMPO_FINE",
        "TEMPO_ESECUZ"
    ]].rename(columns={
        "COMMESSA": "Commessa",
        "STATO_ORDINE": "Stato ordine",
        "QTA_PRODOTTA": "Quantità prodotta",
        "TEMPO_INIZIO": "Inizio lavorazione",
        "TEMPO_FINE": "Fine lavorazione",
        "TEMPO_ESECUZ": "Tempo ciclo (s)"
    })

    chart_df = tl[["COMMESSA", "QTA_PRODOTTA"]].copy().set_index("COMMESSA")
    return timeline_table, chart_df

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
if page == "Dashboard":
    st.title("Dashboard Cella Robotica di Saldatura - Tecnorobot")
    st.markdown("Supervisione ordini, stato della lavorazione e monitoraggio degli avanzamenti.")

    section_header(
        "Stato generale della cella",
        "Vista sintetica della linea di saldatura, con KPI e stato operativo corrente."
    )

    if machine_status.startswith("🔴"):
        st.error(machine_status)
        st.markdown('<span class="badge-alert">Allarme attivo</span>', unsafe_allow_html=True)
    elif machine_status.startswith("🟡"):
        st.warning(machine_status)
        st.markdown('<span class="badge-warn">Attenzione</span>', unsafe_allow_html=True)
    elif machine_status.startswith("🟢"):
        st.success(machine_status)
        st.markdown('<span class="badge-ok">Sistema operativo</span>', unsafe_allow_html=True)
    else:
        st.info(machine_status)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(kpi_card("Ordini da lavorare", to_do_count), unsafe_allow_html=True)
    c2.markdown(kpi_card("Ordine in lavorazione", in_work_count), unsafe_allow_html=True)
    c3.markdown(kpi_card("Ordini completati", completed_count), unsafe_allow_html=True)
    c4.markdown(kpi_card("Pezzi prodotti", pieces_done), unsafe_allow_html=True)
    c5.markdown(kpi_card("Tempo medio ciclo", f"{avg_cycle}s"), unsafe_allow_html=True)

    c6, c7, c8 = st.columns(3)
    c6.markdown(kpi_card("Saturazione macchina", f"{saturazione}%"), unsafe_allow_html=True)
    c7.markdown(kpi_card("OEE stimato", f"{oee_est}%"), unsafe_allow_html=True)
    c8.markdown(kpi_card("Ordini prioritari", int(orders_df["PRIORITARIO"].sum())), unsafe_allow_html=True)

    st.divider()

    top_left, top_right = st.columns([1.5, 1])

    with top_left:
        section_header(
            "Pianificazione ordini",
            "Elenco ordini con stato, sequenza e colori di avanzamento."
        )

        filter_options = ["Tutte"] + sorted(orders_df["COMMESSA"].astype(str).unique().tolist())
        selected_commessa = st.selectbox("Filtra per commessa", filter_options)

        filtered_df = orders_df.copy()
        if selected_commessa != "Tutte":
            filtered_df = filtered_df[filtered_df["COMMESSA"].astype(str) == selected_commessa]

        display_df, styled_df = styled_orders_dataframe(filtered_df)
        st.dataframe(styled_df, use_container_width=True)
        render_download_button(display_df, "Scarica ordini in CSV", "ordini_lavorazione.csv")

    with top_right:
        section_header(
            "Ordine attualmente in lavorazione",
            "Dettaglio dell’unico ordine attivo sulla stazione di saldatura."
        )

        current_view = build_current_order_view(orders_df)
        if len(current_view) > 0:
            st.dataframe(current_view, use_container_width=True)
        else:
            st.write("Nessun ordine attualmente in lavorazione.")

    st.divider()

    bottom_left, bottom_right = st.columns([1.2, 1])

    with bottom_left:
        section_header(
            "Timeline andamento produzione",
            "Sequenza temporale delle lavorazioni con andamento delle quantità prodotte."
        )

        timeline_table, timeline_chart = build_timeline_source(orders_df)
        st.dataframe(timeline_table, use_container_width=True)
        st.bar_chart(timeline_chart)

    with bottom_right:
        section_header(
            "Ordini completati",
            "Storico degli ordini già eseguiti con tempi di inizio, fine e durata ciclo."
        )

        completed_view = build_completed_view(orders_df)
        if len(completed_view) > 0:
            st.dataframe(completed_view, use_container_width=True)
        else:
            st.write("Nessun ordine completato.")

# -------------------------------------------------
# ORDINI
# -------------------------------------------------
elif page == "Ordini":
    st.title("Ordini di Produzione")
    section_header(
        "Elenco completo ordini",
        "Vista completa degli ordini con priorità, sequenza e stato di avanzamento."
    )

    display_df, styled_df = styled_orders_dataframe(orders_df)
    st.dataframe(styled_df, use_container_width=True)
    render_download_button(display_df, "Scarica elenco ordini", "elenco_ordini.csv")

# -------------------------------------------------
# AVANZAMENTI
# -------------------------------------------------
elif page == "Avanzamenti":
    st.title("Avanzamenti Produzione")
    section_header(
        "Avanzamento lavorazioni",
        "Vista operativa dei tempi e dello stato di ciascun ordine."
    )

    progress_df = build_progress_view(orders_df)
    st.dataframe(progress_df, use_container_width=True)
    render_download_button(progress_df, "Scarica avanzamenti", "avanzamenti.csv")

# -------------------------------------------------
# DIAGNOSTICA
# -------------------------------------------------
elif page == "Diagnostica":
    st.title("Diagnostica e Allarmi")
    section_header(
        "Eventi di diagnostica",
        "Segnalazioni, anomalie e allarmi associati agli ordini presenti in lavorazione."
    )

    diag_df = build_diagnostic_view(orders_df)
    if len(diag_df) > 0:
        st.dataframe(diag_df, use_container_width=True)
    else:
        st.success("Nessun allarme presente.")

# -------------------------------------------------
# PIANIFICAZIONE - SOLO ADMIN
# -------------------------------------------------
elif page == "Pianificazione":
    st.title("Pianificazione ordini")
    st.markdown("Area amministratore per priorità, sequenza e supervisione del flusso.")

    st.info(
        "La selezione dell’ordine in lavorazione rappresenta una logica di supervisione e "
        "preparazione del flusso. Non costituisce un comando diretto al robot."
    )

    section_header(
        "1. Modalità di pianificazione",
        "Definizione della logica di ordinamento del flusso: FIFO oppure gestione manuale."
    )

    selected_mode = st.radio(
        "Seleziona la modalità",
        ["FIFO", "Manuale"],
        index=0 if st.session_state.planning_mode == "FIFO" else 1,
        horizontal=True
    )

    if st.button("Applica modalità di pianificazione"):
        st.session_state.planning_mode = selected_mode

        temp_df = st.session_state.orders_df.copy()
        if selected_mode == "FIFO":
            temp_df = apply_fifo_sequence(temp_df)
        else:
            temp_df = apply_manual_sequence(temp_df)

        st.session_state.orders_df = temp_df
        st.success(f"Modalità impostata su {selected_mode}.")
        st.rerun()

    section_header(
        "2. Priorità ordine",
        "Seleziona l’ordine che deve essere considerato prioritario per rilevanza o urgenza."
    )

    selectable_priority_df = orders_df[orders_df["STATO_ORDINE"] != "COMPLETATO"].copy()

    if len(selectable_priority_df) > 0:
        priority_map = {
            f"{row.COMMESSA} - {row.ARTICOLO}": row.ID
            for row in selectable_priority_df.itertuples()
        }

        priority_label = st.selectbox(
            "Seleziona l’ordine prioritario",
            options=list(priority_map.keys())
        )

        if st.button("Assegna priorità"):
            selected_id = priority_map[priority_label]
            temp_df = set_priority(st.session_state.orders_df.copy(), selected_id)

            if st.session_state.planning_mode == "FIFO":
                temp_df = apply_fifo_sequence(temp_df)
            else:
                temp_df = apply_manual_sequence(temp_df)

            st.session_state.orders_df = temp_df
            st.success("Ordine prioritario aggiornato.")
            st.rerun()
    else:
        st.write("Nessun ordine disponibile per la priorità.")

    section_header(
        "3. Definisci sequenza",
        "In modalità Manuale puoi modificare direttamente l’ordine di lavorazione degli ordini non completati."
    )

    if st.session_state.planning_mode == "Manuale":
        waiting_manual = orders_df[orders_df["STATO_ORDINE"] != "COMPLETATO"].copy()
        edit_df = waiting_manual[[
            "ID", "COMMESSA", "ARTICOLO", "SEQUENZA", "PRIORITARIO", "STATO_ORDINE"
        ]].rename(columns={
            "COMMESSA": "Commessa",
            "ARTICOLO": "Codice articolo",
            "SEQUENZA": "Definisci sequenza",
            "PRIORITARIO": "Prioritario",
            "STATO_ORDINE": "Stato"
        })

        edited_df = st.data_editor(
            edit_df,
            use_container_width=True,
            hide_index=True,
            disabled=["ID", "Commessa", "Codice articolo", "Prioritario", "Stato"],
            key="manual_sequence_editor"
        )

        if st.button("Salva sequenza manuale"):
            temp_df = st.session_state.orders_df.copy()

            for _, row in edited_df.iterrows():
                temp_df.loc[temp_df["ID"] == row["ID"], "SEQUENZA"] = int(row["Definisci sequenza"])

            temp_df = apply_manual_sequence(temp_df)
            st.session_state.orders_df = temp_df
            st.success("Sequenza manuale aggiornata.")
            st.rerun()
    else:
        st.caption("La sequenza manuale è disponibile solo quando la modalità è impostata su Manuale.")

    section_header(
        "4. Ordine attualmente in lavorazione",
        "Impostazione dell’ordine preso in carico dal flusso di supervisione."
    )

    selectable_work_df = orders_df[orders_df["STATO_ORDINE"] != "COMPLETATO"].copy()

    if len(selectable_work_df) > 0:
        work_map = {
            f"{row.COMMESSA} - {row.ARTICOLO}": row.ID
            for row in selectable_work_df.itertuples()
        }

        work_label = st.selectbox(
            "Seleziona l’ordine da mettere in lavorazione",
            options=list(work_map.keys())
        )

        if st.button("Imposta ordine in lavorazione"):
            selected_id = work_map[work_label]
            temp_df = set_order_in_work(st.session_state.orders_df.copy(), selected_id)

            if st.session_state.planning_mode == "FIFO":
                temp_df = apply_fifo_sequence(temp_df)
            else:
                temp_df = apply_manual_sequence(temp_df)

            st.session_state.orders_df = temp_df
            st.success("Ordine impostato come in lavorazione nel flusso di supervisione.")
            st.rerun()
    else:
        st.write("Nessun ordine disponibile.")

    section_header(
        "5. Notifiche email",
        "Configurazione del recapito dell’amministratore per la segnalazione di fine lavorazione."
    )

    admin_email = st.text_input(
        "Email amministratore per fine lavorazione",
        value=st.session_state.admin_email
    )

    if st.button("Salva email amministratore"):
        st.session_state.admin_email = admin_email
        st.success("Email amministratore salvata.")

    st.caption(
        "La notifica email è predisposta per l’integrazione futura. "
        "In questa versione demo non viene inviata realmente."
    )

    section_header(
        "6. Fine lavorazione (solo demo)",
        "Simulazione del completamento dell’ordine attualmente in lavorazione per test del flusso."
    )

    current_in_work = orders_df[orders_df["STATO_ORDINE"] == "IN_LAVORAZIONE"].copy()

    if len(current_in_work) > 0:
        current_label = f"{current_in_work.iloc[0]['COMMESSA']} - {current_in_work.iloc[0]['ARTICOLO']}"
        st.write(f"Ordine attualmente in lavorazione: **{current_label}**")

        if st.button("Segna ordine corrente come completato (solo demo)"):
            temp_df, completed_order = complete_current_order_demo(st.session_state.orders_df.copy())

            if completed_order is not None:
                if st.session_state.planning_mode == "FIFO":
                    temp_df = apply_fifo_sequence(temp_df)
                else:
                    temp_df = apply_manual_sequence(temp_df)

                st.session_state.orders_df = temp_df

                result = send_completion_email(completed_order, st.session_state.admin_email)
                st.session_state.notification_log.append(result["message"])

                st.success("Ordine segnato come completato.")
                st.info(result["message"])
                st.rerun()
    else:
        st.write("Nessun ordine attualmente in lavorazione.")
