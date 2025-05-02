import pyodbc

def load_item_data():
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=HP\TWDEEAGN;'
        r'DATABASE=InventoryDB;'
        r'Trusted_Connection=yes;'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ItemName, HSNCode FROM Purchases")
    rows = cursor.fetchall()
    conn.close()
    return {row.ItemName: row.HSNCode for row in rows}

item_data = load_item_data()
