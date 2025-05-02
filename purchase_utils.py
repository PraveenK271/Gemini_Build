from db_config import get_connection

def insert_purchase(data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO Purchases (Date, SupplierName, ItemName, HSNCode, Quantity, UnitPrice, GST)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', data['Date'], data['SupplierName'], data['ItemName'], data['HSNCode'],
         data['Quantity'], data['UnitPrice'], data['GST'])

    conn.commit()
    conn.close()


def update_purchase(purchase_id, data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE Purchases
        SET Date = ?, SupplierName = ?, ItemName = ?, HSNCode = ?, Quantity = ?, UnitPrice = ?, GST = ?
        WHERE PurchaseID = ?
    ''', data['Date'], data['SupplierName'], data['ItemName'], data['HSNCode'],
         data['Quantity'], data['UnitPrice'], data['GST'], purchase_id)

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected
