import pandas as pd


def stato_commessa(flag):
    if flag == 1:
        return "In lavorazione"
    elif flag == 199:
        return "Terminata stazione 1"
    elif flag == 299:
        return "Terminata stazione 2"
    return "Altro"


def prepara_avanzamenti(df_av):
    df_av = df_av.copy()

    # Timestamp ricostruito da data e ora
    df_av["timestamp_evento"] = pd.to_datetime(
        df_av["DATA_AA"].astype(str) + "-" +
        df_av["DATA_MM"].astype(str).str.zfill(2) + "-" +
        df_av["DATA_GG"].astype(str).str.zfill(2) + " " +
        df_av["HH"].astype(str).str.zfill(2) + ":" +
        df_av["MIN"].astype(str).str.zfill(2) + ":" +
        df_av["SEC"].astype(str).str.zfill(2),
        errors="coerce"
    )

    # Stato commessa
    df_av["STATO_COMMESSA"] = df_av["FLAG_FINITO"].apply(stato_commessa)

    # Tipo record
    df_av["TIPO_RECORD"] = df_av["ALLARME1"].apply(
        lambda x: "Diagnostica" if pd.notna(x) and str(x).strip() != "" else "Produzione"
    )

    # Tempo inizio
    df_av["TEMPO_INIZIO"] = df_av["timestamp_evento"] - pd.to_timedelta(
        df_av["TEMPO_ESECUZ"].fillna(0), unit="s"
    )

    # Tempo fine solo per commesse concluse
    df_av["TEMPO_FINE"] = df_av["timestamp_evento"]
    df_av.loc[df_av["FLAG_FINITO"] == 1, "TEMPO_FINE"] = pd.NaT

    # Ultimo aggiornamento utile per commesse in corso
    df_av["ULTIMO_AGGIORNAMENTO"] = df_av["timestamp_evento"]

    return df_av


def unisci_dati(df_odp, df_av):
    df_merge = df_odp.merge(
        df_av,
        how="left",
        left_on="ID",
        right_on="ID_SQL",
        suffixes=("_ODP", "_AV")
    )

    df_merge["SCOSTAMENTO_QTA"] = (
        df_merge["QUANT_DA_PRODURRE"] - df_merge["QTA_PRODOTTA"].fillna(0)
    )

    return df_merge
