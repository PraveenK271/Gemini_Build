import pandas as pd
import pyodbc

# Read the Excel file using pandas and openpyxl backend
df = pd.read_excel('purchase_data.xlsx', engine='openpyxl')

# Connect to MSSQL database
conn = pyodbc.connect(
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=HP\TWDEEAGN;'
    r'DATABASE=InventoryDB;'
    r'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# Insert rows into Purchases table
for index, row in df.iterrows():
    cursor.execute('''
        INSERT INTO Purchases (Date, SupplierName, ItemName, HSNCode, Quantity, UnitPrice, GST)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', row['Date'], row['SupplierName'], row['ItemName'], row['HSNCode'],
         row['Quantity'], row['UnitPrice'], row['GST'])

conn.commit()
cursor.close()
conn.close()

print("Data imported successfully!")
    