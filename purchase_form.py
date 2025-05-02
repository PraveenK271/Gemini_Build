import tkinter as tk
from tkinter import messagebox
from purchase_utils import insert_purchase, update_purchase

class PurchaseForm:
    def __init__(self, root):
        self.root = root
        self.root.title("Purchase Entry Form")

        # Input fields
        self.fields = {
            "PurchaseID": tk.Entry(root),
            "Date": tk.Entry(root),
            "SupplierName": tk.Entry(root),
            "ItemName": tk.Entry(root),
            "HSNCode": tk.Entry(root),
            "Quantity": tk.Entry(root),
            "UnitPrice": tk.Entry(root),
            "GST": tk.Entry(root)
        }

        # Draw form
        labels = ["Purchase ID (only for update)", "Date (YYYY-MM-DD)", "Supplier Name",
                  "Item Name", "HSN Code", "Quantity", "Unit Price", "GST (%)"]

        for idx, (label, key) in enumerate(zip(labels, self.fields)):
            tk.Label(root, text=label).grid(row=idx, column=0, sticky="w")
            self.fields[key].grid(row=idx, column=1)

        # Buttons
        tk.Button(root, text="Add Purchase", command=self.add).grid(row=8, column=0, pady=10)
        tk.Button(root, text="Update Purchase", command=self.update).grid(row=8, column=1)

    def add(self):
        try:
            data = self.get_form_data(include_id=False)
            insert_purchase(data)
            messagebox.showinfo("Success", "Purchase added!")
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update(self):
        try:
            data = self.get_form_data(include_id=True)
            purchase_id = int(self.fields['PurchaseID'].get())
            result = update_purchase(purchase_id, data)
            if result == 0:
                messagebox.showwarning("Not Found", "No record with that ID.")
            else:
                messagebox.showinfo("Success", "Purchase updated!")
            self.clear_fields()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_form_data(self, include_id=True):
        data = {
            'Date': self.fields['Date'].get(),
            'SupplierName': self.fields['SupplierName'].get(),
            'ItemName': self.fields['ItemName'].get(),
            'HSNCode': self.fields['HSNCode'].get(),
            'Quantity': int(self.fields['Quantity'].get()),
            'UnitPrice': float(self.fields['UnitPrice'].get()),
            'GST': float(self.fields['GST'].get())
        }
        return data

    def clear_fields(self):
        for field in self.fields.values():
            field.delete(0, tk.END)
