import pyodbc

server = "TECNOROBOT-PC"
database = "ROBOT_E12345"

conn_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
)

try:
    conn = pyodbc.connect(conn_string)
    print("Connessione riuscita!")

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.tables")

    print("Tabelle trovate:")
    for row in cursor.fetchall():
        print(row[0])

except Exception as e:
    print("Errore di connessione:")
    print(e)
