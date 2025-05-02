import pyodbc

def get_connection():
    return pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=HP\TWDEEAGN;'
        r'DATABASE=InventoryDB;'
        r'Trusted_Connection=yes;'
    )
