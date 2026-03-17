
import pandas as pd


def prepare_orders(df_orders):
    df = df_orders.copy()

    for col in ["DATA_INSERIMENTO", "TEMPO_INIZIO", "TEMPO_FINE"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "PRIORITARIO" in df.columns:
        df["PRIORITARIO"] = df["PRIORITARIO"].fillna(False).astype(bool)

    if "SEQUENZA" in df.columns:
        df["SEQUENZA"] = pd.to_numeric(df["SEQUENZA"], errors="coerce").fillna(999).astype(int)

    if "QTA_PRODOTTA" in df.columns:
        df["QTA_PRODOTTA"] = pd.to_numeric(df["QTA_PRODOTTA"], errors="coerce").fillna(0)

    if "QUANT_DA_PRODURRE" in df.columns:
        df["QUANT_DA_PRODURRE"] = pd.to_numeric(df["QUANT_DA_PRODURRE"], errors="coerce").fillna(0)

    if "TEMPO_ESECUZ" in df.columns:
        df["TEMPO_ESECUZ"] = pd.to_numeric(df["TEMPO_ESECUZ"], errors="coerce").fillna(0)

    if "ALLARME1" not in df.columns:
        df["ALLARME1"] = ""

    return normalize_single_active(df)


def normalize_single_active(df):
    df = df.copy()

    attivi = df[df["STATO_ORDINE"] == "IN_LAVORAZIONE"].index.tolist()
    if len(attivi) > 1:
        first_active = attivi[0]
        for idx in attivi[1:]:
            df.loc[idx, "STATO_ORDINE"] = "DA_LAVORARE"
            df.loc[idx, "TEMPO_INIZIO"] = pd.NaT
            df.loc[idx, "TEMPO_FINE"] = pd.NaT

    # In lavorazione non deve avere tempo fine
    df.loc[df["STATO_ORDINE"] == "IN_LAVORAZIONE", "TEMPO_FINE"] = pd.NaT

    return df


def apply_fifo_sequence(df):
    df = df.copy()

    current_active = df[df["STATO_ORDINE"] == "IN_LAVORAZIONE"].copy()
    waiting = df[df["STATO_ORDINE"] == "DA_LAVORARE"].copy()
    completed = df[df["STATO_ORDINE"] == "COMPLETATO"].copy()

    waiting = waiting.sort_values(
        by=["PRIORITARIO", "DATA_INSERIMENTO", "ID"],
        ascending=[False, True, True]
    )

    seq = 1

    if len(current_active) > 0:
        active_idx = current_active.index[0]
        df.loc[active_idx, "SEQUENZA"] = seq
        seq += 1

    for idx in waiting.index:
        df.loc[idx, "SEQUENZA"] = seq
        seq += 1

    for idx in completed.sort_values(by=["TEMPO_FINE", "ID"], ascending=[False, True]).index:
        df.loc[idx, "SEQUENZA"] = seq
        seq += 1

    return df


def apply_manual_sequence(df):
    df = df.copy()

    current_active = df[df["STATO_ORDINE"] == "IN_LAVORAZIONE"].copy()
    waiting = df[df["STATO_ORDINE"] == "DA_LAVORARE"].copy()
    completed = df[df["STATO_ORDINE"] == "COMPLETATO"].copy()

    waiting = waiting.sort_values(
        by=["PRIORITARIO", "SEQUENZA", "ID"],
        ascending=[False, True, True]
    )

    seq = 1

    if len(current_active) > 0:
        active_idx = current_active.index[0]
        df.loc[active_idx, "SEQUENZA"] = seq
        seq += 1

    for idx in waiting.index:
        df.loc[idx, "SEQUENZA"] = seq
        seq += 1

    for idx in completed.sort_values(by=["TEMPO_FINE", "ID"], ascending=[False, True]).index:
        df.loc[idx, "SEQUENZA"] = seq
        seq += 1

    return df


def set_priority(df, order_id):
    df = df.copy()
    df["PRIORITARIO"] = False

    if order_id is not None:
        df.loc[df["ID"] == order_id, "PRIORITARIO"] = True

    return df


def set_order_in_work(df, order_id):
    df = df.copy()

    if order_id is None:
        return df

    # solo ordini non completati
    selected = df[df["ID"] == order_id]
    if selected.empty:
        return df

    if selected.iloc[0]["STATO_ORDINE"] == "COMPLETATO":
        return df

    # tutti gli ordini in lavorazione tornano da lavorare
    mask_active = df["STATO_ORDINE"] == "IN_LAVORAZIONE"
    df.loc[mask_active, "STATO_ORDINE"] = "DA_LAVORARE"
    df.loc[mask_active, "TEMPO_FINE"] = pd.NaT

    # ordine selezionato diventa in lavorazione
    now_ts = pd.Timestamp.now().floor("s")
    df.loc[df["ID"] == order_id, "STATO_ORDINE"] = "IN_LAVORAZIONE"
    df.loc[df["ID"] == order_id, "TEMPO_FINE"] = pd.NaT

    # solo se non aveva già inizio, lo impostiamo
    if pd.isna(df.loc[df["ID"] == order_id, "TEMPO_INIZIO"]).all():
        df.loc[df["ID"] == order_id, "TEMPO_INIZIO"] = now_ts

    return normalize_single_active(df)


def complete_current_order_demo(df):
    df = df.copy()
    current = df[df["STATO_ORDINE"] == "IN_LAVORAZIONE"]

    if current.empty:
        return df, None

    idx = current.index[0]
    now_ts = pd.Timestamp.now().floor("s")
    start_ts = df.loc[idx, "TEMPO_INIZIO"]

    if pd.isna(start_ts):
        start_ts = now_ts
        df.loc[idx, "TEMPO_INIZIO"] = start_ts

    elapsed = int((now_ts - start_ts).total_seconds())

    df.loc[idx, "STATO_ORDINE"] = "COMPLETATO"
    df.loc[idx, "TEMPO_FINE"] = now_ts
    df.loc[idx, "TEMPO_ESECUZ"] = max(elapsed, 1)
    df.loc[idx, "QTA_PRODOTTA"] = df.loc[idx, "QUANT_DA_PRODURRE"]

    completed_order = df.loc[idx].to_dict()
    return df, completed_order


def get_machine_status(df):
    active_order = df[df["STATO_ORDINE"] == "IN_LAVORAZIONE"]
    any_alarm = df["ALLARME1"].fillna("").astype(str).str.strip().ne("").any()
    waiting_orders = (df["STATO_ORDINE"] == "DA_LAVORARE").sum()

    if any_alarm:
        return "🔴 Con allarme attivo"
    if len(active_order) > 0:
        return "🟢 In lavorazione"
    if waiting_orders > 0:
        return "🟡 In attesa ordine"
    return "⚪ Nessun ordine pianificato"


def get_orders_for_display(df, planning_mode):
    df = df.copy()

    if planning_mode == "FIFO":
        df = apply_fifo_sequence(df)
    else:
        df = apply_manual_sequence(df)

    status_rank = {
        "IN_LAVORAZIONE": 0,
        "DA_LAVORARE": 1,
        "COMPLETATO": 2
    }

    df["STATUS_RANK"] = df["STATO_ORDINE"].map(status_rank).fillna(9)
    df = df.sort_values(by=["STATUS_RANK", "SEQUENZA", "ID"], ascending=[True, True, True]).drop(columns=["STATUS_RANK"])

    return df


def style_rows_by_status(row):
    status = row["Stato ordine"]

    if status == "COMPLETATO":
        return ["background-color: #eaf7ea"] * len(row)
    elif status == "IN_LAVORAZIONE":
        return ["background-color: #fff6d8"] * len(row)
    else:
        return ["background-color: white"] * len(row)


def build_orders_table(df):
    view = df.copy()

    view["Prioritario"] = view["PRIORITARIO"].map({True: "Sì", False: "No"})

    view = view[[
        "ID",
        "SEQUENZA",
        "COMMESSA",
        "DES_PROD",
        "ARTICOLO",
        "QUANT_DA_PRODURRE",
        "QTA_PRODOTTA",
        "PRIORITARIO",
        "STATO_ORDINE",
        "TEMPO_INIZIO",
        "TEMPO_FINE",
        "TEMPO_ESECUZ"
    ]].rename(columns={
        "ID": "ID",
        "SEQUENZA": "Sequenza",
        "COMMESSA": "Commessa",
        "DES_PROD": "Descrizione pezzo",
        "ARTICOLO": "Codice articolo",
        "QUANT_DA_PRODURRE": "Quantità da produrre",
        "QTA_PRODOTTA": "Quantità prodotta",
        "PRIORITARIO": "Prioritario",
        "STATO_ORDINE": "Stato ordine",
        "TEMPO_INIZIO": "Inizio lavorazione",
        "TEMPO_FINE": "Fine lavorazione",
        "TEMPO_ESECUZ": "Tempo ciclo (s)"
    })

    return view
