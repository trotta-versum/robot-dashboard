import pandas as pd
import pyodbc

# -------------------------------------------------
# CONFIGURAZIONE
# -------------------------------------------------
USE_SQL_SERVER = False
SQL_SERVER = "INSERISCI_SERVER"
SQL_DATABASE = "ROBOT_E12345"
SQL_DRIVER = "ODBC Driver 17 for SQL Server"

# -------------------------------------------------
# DATI SIMULATI - ODP
# -------------------------------------------------
def get_odp_data():
    return pd.DataFrame([
        {
            "ID": 1,
            "PROGRAMMA": "PRG_SALD_01",
            "COMMESSA": "COMM_2026_001",
            "DES_PROD": "Telaio supporto metallico",
            "ARTICOLO": "ART_1001",
            "QUANT_DA_PRODURRE": 20
        },
        {
            "ID": 2,
            "PROGRAMMA": "PRG_SALD_02",
            "COMMESSA": "COMM_2026_002",
            "DES_PROD": "Staffa laterale",
            "ARTICOLO": "ART_1002",
            "QUANT_DA_PRODURRE": 35
        },
        {
            "ID": 3,
            "PROGRAMMA": "PRG_SALD_03",
            "COMMESSA": "COMM_2026_003",
            "DES_PROD": "Piastra base",
            "ARTICOLO": "ART_1003",
            "QUANT_DA_PRODURRE": 15
        }
    ])


# -------------------------------------------------
# DATI SIMULATI - AVANZAMENTI
# Nota:
# - un record con ALLARME1 valorizzato farà apparire
#   lo stato macchina come "🔴 Con allarme attivo"
# -------------------------------------------------
def get_avanzamenti_data():
    return pd.DataFrame([
        {
            "ID_SQL": 1,
            "DATA_GG": 16,
            "DATA_MM": 3,
            "DATA_AA": 2026,
            "HH": 8,
            "MIN": 15,
            "SEC": 0,
            "OPERATORE": "OP01",
            "STAZIONE": "ST1",
            "PROGRAMMA": "PRG_SALD_01",
            "COMMESSA": "COMM_2026_001",
            "ARTICOLO": "ART_1001",
            "TEMPO_ESECUZ": 180,
            "QTA_PRODOTTA": 12,
            "FLAG_FINITO": 1,
            "ALLARME1": ""
        },
        {
            "ID_SQL": 2,
            "DATA_GG": 16,
            "DATA_MM": 3,
            "DATA_AA": 2026,
            "HH": 9,
            "MIN": 40,
            "SEC": 0,
            "OPERATORE": "OP02",
            "STAZIONE": "ST2",
            "PROGRAMMA": "PRG_SALD_02",
            "COMMESSA": "COMM_2026_002",
            "ARTICOLO": "ART_1002",
            "TEMPO_ESECUZ": 240,
            "QTA_PRODOTTA": 35,
            "FLAG_FINITO": 299,
            "ALLARME1": ""
        },
        {
            "ID_SQL": 3,
            "DATA_GG": 16,
            "DATA_MM": 3,
            "DATA_AA": 2026,
            "HH": 10,
            "MIN": 5,
            "SEC": 0,
            "OPERATORE": "OP03",
            "STAZIONE": "ST1",
            "PROGRAMMA": "PRG_SALD_03",
            "COMMESSA": "COMM_2026_003",
            "ARTICOLO": "ART_1003",
            "TEMPO_ESECUZ": 0,
            "QTA_PRODOTTA": 0,
            "FLAG_FINITO": 1,
            "ALLARME1": "Verifica posizionamento pezzo"
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
def get_odp_from_sql():
    if not USE_SQL_SERVER:
        return None

    try:
        conn = get_sql_connection()
        query = "SELECT * FROM ODP"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print("Errore lettura ODP da SQL Server:", e)
        return None


# -------------------------------------------------
# LETTURA SQL - AVANZAMENTI
# -------------------------------------------------
def get_avanzamenti_from_sql():
    if not USE_SQL_SERVER:
        return None

    try:
        conn = get_sql_connection()
        query = "SELECT * FROM AVANZAMENTI"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print("Errore lettura AVANZAMENTI da SQL Server:", e)
        return None
