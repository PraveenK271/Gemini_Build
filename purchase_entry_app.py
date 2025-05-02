import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import pyodbc

# --- Database Connection (adjust as needed) ---
def get_connection():
    return pyodbc.connect("DRIVER={SQL Server};SERVER=localhost;DATABASE=YourDB;Trusted_Connection=yes")

# --- App to Add Purchase Entries ---
class PurchaseEntryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Purchase Entry")

        self.row_counter = 0
        self.purchase_rows = []

        self.build_table()
        self.build_buttons()

    def build_table(self):
        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(pady=10)

        headers = ["S.No", "HSN Code", "Item Description", "Quantity", "Unit Price (Ex. GST)", "GST %", "Price Inc. GST", "Biller", "Date", "Month", "FY"]
        for col, header in enumerate(headers):
            tk.Label(self.table_frame, text=header, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=2, pady=2)

        self.add_row()

    def add_row(self):
        row_widgets = {}
        r = self.row_counter + 1

        sn_entry = ttk.Entry(self.table_frame, width=5)
        sn_entry.insert(0, str(r))
        sn_entry.config(state='readonly')
        sn_entry.grid(row=r, column=0)
        row_widgets['SNo'] = sn_entry

        for idx, field in enumerate(["HSN", "Item", "Qty", "Price", "GST", "Total", "Biller", "Date", "Month", "FY"], start=1):
            if field == "Date":
                date_picker = DateEntry(self.table_frame, date_pattern="yyyy-mm-dd", width=12)
                date_picker.set_date(datetime.today())
                date_picker.grid(row=r, column=idx)
                row_widgets[field] = date_picker
            elif field == "Month":
                month_var = tk.StringVar()
                entry = ttk.Entry(self.table_frame, textvariable=month_var, width=15)
                entry.grid(row=r, column=idx)
                month_var.set(datetime.today().strftime("%B"))
                row_widgets[field] = entry
            elif field == "FY":
                fy_var = tk.StringVar()
                entry = ttk.Entry(self.table_frame, textvariable=fy_var, width=15)
                entry.grid(row=r, column=idx)
                today = datetime.today()
                fy = f"{today.year-1}-{today.year}" if today.month < 4 else f"{today.year}-{today.year+1}"
                fy_var.set(fy)
                row_widgets[field] = entry
            else:
                var = tk.StringVar()
                entry = ttk.Entry(self.table_frame, textvariable=var, width=15)
                entry.grid(row=r, column=idx)
                row_widgets[field] = entry

        self.purchase_rows.append(row_widgets)
        self.row_counter += 1

    def save_to_db(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            for row in self.purchase_rows:
                cursor.execute("""
                    INSERT INTO purchase_data (SNo, HSNCode, ItemDescription, Quantity, UnitPrice, GSTPercent,
                                               PriceIncGST, Biller, Date, Month, FinancialYear)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                int(row['SNo'].get()),
                row['HSN'].get(), row['Item'].get(), int(row['Qty'].get()),
                float(row['Price'].get()), float(row['GST'].get()), float(row['Total'].get()),
                row['Biller'].get(), row['Date'].get_date(), row['Month'].get(), row['FY'].get())

            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Purchase data saved to database.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def build_buttons(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add Row", command=self.add_row).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Save to Database", command=self.save_to_db).grid(row=0, column=1, padx=10)

# --- Run App ---
if __name__ == '__main__':
    root = tk.Tk()
    app = PurchaseEntryApp(root)
    root.mainloop()
