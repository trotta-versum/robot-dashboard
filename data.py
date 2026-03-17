import pandas as pd
import pyodbc

# -------------------------------------------------
# CONFIGURAZIONE SQL SERVER
# -------------------------------------------------
USE_SQL_SERVER = False
SQL_SERVER = "INSERISCI_SERVER"
SQL_DATABASE = "ROBOT_E12345"
SQL_DRIVER = "ODBC Driver 17 for SQL Server"

# -------------------------------------------------
# ORDINI INIZIALI DEMO
# -------------------------------------------------
def get_orders_data():
    return pd.DataFrame([
        {
            "ID": 1,
            "PROGRAMMA": "PRG_SALD_01",
            "COMMESSA": "COMM_2026_001",
            "DES_PROD": "Telaio supporto metallico",
            "ARTICOLO": "ART_1001",
            "QUANT_DA_PRODURRE": 20,
            "QTA_PRODOTTA": 20,
            "STATO_ORDINE": "COMPLETATO",
            "PRIORITARIO": False,
            "SEQUENZA": 1,
            "STAZIONE": "ST1",
            "DATA_INSERIMENTO": "2026-03-15 08:00:00",
            "TEMPO_INIZIO": "2026-03-15 08:10:00",
            "TEMPO_FINE": "2026-03-15 08:16:00",
            "TEMPO_ESECUZ": 360,
            "ALLARME1": ""
        },
        {
            "ID": 2,
            "PROGRAMMA": "PRG_SALD_02",
            "COMMESSA": "COMM_2026_002",
            "DES_PROD": "Staffa laterale",
            "ARTICOLO": "ART_1002",
            "QUANT_DA_PRODURRE": 35,
            "QTA_PRODOTTA": 12,
            "STATO_ORDINE": "IN_LAVORAZIONE",
            "PRIORITARIO": False,
            "SEQUENZA": 2,
            "STAZIONE": "ST1",
            "DATA_INSERIMENTO": "2026-03-16 08:00:00",
            "TEMPO_INIZIO": "2026-03-16 09:30:00",
            "TEMPO_FINE": None,
            "TEMPO_ESECUZ": 180,
            "ALLARME1": ""
        },
        {
            "ID": 3,
            "PROGRAMMA": "PRG_SALD_03",
            "COMMESSA": "COMM_2026_003",
            "DES_PROD": "Piastra base",
            "ARTICOLO": "ART_1003",
            "QUANT_DA_PRODURRE": 15,
            "QTA_PRODOTTA": 0,
            "STATO_ORDINE": "DA_LAVORARE",
            "PRIORITARIO": True,
            "SEQUENZA": 3,
            "STAZIONE": "ST1",
            "DATA_INSERIMENTO": "2026-03-16 09:00:00",
            "TEMPO_INIZIO": None,
            "TEMPO_FINE": None,
            "TEMPO_ESECUZ": 0,
            "ALLARME1": ""
        },
        {
            "ID": 4,
            "PROGRAMMA": "PRG_SALD_04",
            "COMMESSA": "COMM_2026_004",
            "DES_PROD": "Supporto angolare",
            "ARTICOLO": "ART_1004",
            "QUANT_DA_PRODURRE": 18,
            "QTA_PRODOTTA": 0,
            "STATO_ORDINE": "DA_LAVORARE",
            "PRIORITARIO": False,
            "SEQUENZA": 4,
            "STAZIONE": "ST1",
            "DATA_INSERIMENTO": "2026-03-16 10:00:00",
            "TEMPO_INIZIO": None,
            "TEMPO_FINE": None,
            "TEMPO_ESECUZ": 0,
            "ALLARME1": ""
        }
    ])


# -------------------------------------------------
# CONNESSIONE SQL SERVER
# -------------------------------------------------
def get_sql_connection():
    return pyodbc.connect(
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        "Trusted_Connection=yes;",
        timeout=3
    )


# -------------------------------------------------
# LETTURA SQL - ODP
# -------------------------------------------------
def get_orders_from_sql():
    if not USE_SQL_SERVER:
        return None

    try:
        conn = get_sql_connection()
        query = "SELECT * FROM ODP"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print("Errore lettura ordini da SQL Server:", e)
        return None
