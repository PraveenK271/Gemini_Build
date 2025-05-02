import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyodbc
from tkcalendar import DateEntry
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap
from num2words import num2words

from invoice_data import item_data
from db_config import get_connection
from seller_config import SELLER_DETAILS
from invoice_config import INVOICE_FORMAT, BANK_DETAILS
from create_invoice_pdf import create_invoice


class InvoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice Generator")
        self.root.geometry("1000x700")

        self.invoice_rows = []
        self.row_counter = 0

        # Buyer inputs
        self.buyer_name = tk.StringVar()
        self.buyer_gstin = tk.StringVar()
        self.buyer_address = tk.StringVar()
        self.buyer_phone = tk.StringVar()

        # Invoice details
        self.invoice_number = tk.StringVar()
        self.invoice_date = tk.StringVar()


        # Seller (constant) from config
        self.seller_name = tk.StringVar(value=SELLER_DETAILS['name'])
        self.seller_gstin = tk.StringVar(value=SELLER_DETAILS['gstin'])
        self.seller_address = tk.StringVar(value=SELLER_DETAILS['address'])
        self.seller_phone = tk.StringVar(value=SELLER_DETAILS['phone'])

        # GST & totals
        self.txn_type_var = tk.StringVar(value="Intra-state")
        self.gst_entry = tk.StringVar(value="18")
        self.cgst_var = tk.StringVar()
        self.sgst_var = tk.StringVar()
        self.igst_var = tk.StringVar()
        self.grand_total_var = tk.StringVar()

        # Build UI
        self.build_buyer_seller_section()
        self.build_header()
        self.build_table()
        self.build_gst_section()
        self.build_buttons()

    def build_buyer_seller_section(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        # Seller Info (read-only)
        tk.Label(frame, text="Seller Info", font=("Arial", 10, "bold"))\
          .grid(row=0, column=0, columnspan=2)
        tk.Label(frame, text="Name:").grid(row=1, column=0, sticky="e")
        tk.Label(frame, text=self.seller_name.get(), width=40,
                 anchor="w", relief="sunken").grid(row=1, column=1)
        tk.Label(frame, text="GSTIN:").grid(row=2, column=0, sticky="e")
        tk.Label(frame, text=self.seller_gstin.get(), width=40,
                 anchor="w", relief="sunken").grid(row=2, column=1)
        tk.Label(frame, text="Address:").grid(row=3, column=0, sticky="e")
        tk.Label(frame, text=self.seller_address.get(), width=40,
                 anchor="w", relief="sunken").grid(row=3, column=1)
        tk.Label(frame, text="Phone:").grid(row=4, column=0, sticky="e")
        tk.Label(frame, text=self.seller_phone.get(), width=40,
                 anchor="w", relief="sunken").grid(row=4, column=1)

        # Buyer Info (editable)
        tk.Label(frame, text="Buyer Info", font=("Arial", 10, "bold"))\
          .grid(row=0, column=2, columnspan=2)
        tk.Label(frame, text="Name:").grid(row=1, column=2, sticky="e")
        tk.Entry(frame, textvariable=self.buyer_name, width=40)\
          .grid(row=1, column=3)
        tk.Label(frame, text="GSTIN:").grid(row=2, column=2, sticky="e")
        tk.Entry(frame, textvariable=self.buyer_gstin, width=40).grid(row=2, column=3)
        self.buyer_gstin.trace_add("write", self.lookup_buyer_by_gstin)
        tk.Label(frame, text="Address:").grid(row=3, column=2, sticky="e")
        tk.Entry(frame, textvariable=self.buyer_address, width=40)\
          .grid(row=3, column=3)
        tk.Label(frame, text="Phone:").grid(row=4, column=2, sticky="e")
        tk.Entry(frame, textvariable=self.buyer_phone, width=40)\
          .grid(row=4, column=3)

        # Invoice Number & Date
        tk.Label(frame, text="Invoice No:").grid(row=5, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.invoice_number, width=20).grid(row=5, column=1)

        tk.Label(frame, text="Invoice Date:").grid(row=5, column=2, sticky="e")
        tk.Entry(frame, textvariable=self.invoice_date, width=20).grid(row=5, column=3)
        self.invoice_date.set(datetime.today().strftime("%d/%m/%Y"))
    

    def build_header(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        tk.Label(frame, text="Invoice Entry", font=("Arial", 18)).pack()

    def build_table(self):
        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(pady=10)
        headers = ["S.No", "Item Description", "HSN Code", "Quantity", "Unit Price", "Total"]
        for col, header in enumerate(headers):
            tk.Label(self.table_frame, text=header,
                     font=("Arial", 10, "bold"))\
              .grid(row=0, column=col, padx=5, pady=5)
        self.add_invoice_row()

    def build_gst_section(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        tk.Label(frame, text="Transaction Type:").grid(row=0, column=0, padx=5, sticky="e")
        ttk.OptionMenu(frame, self.txn_type_var,
                       "Intra-state", "Intra-state", "Inter-state")\
           .grid(row=0, column=1)
        tk.Label(frame, text="GST Rate (%):").grid(row=0, column=2, padx=5, sticky="e")
        tk.Entry(frame, textvariable=self.gst_entry, width=10)\
          .grid(row=0, column=3, padx=5)
        tk.Label(frame, textvariable=self.cgst_var,
                 font=("Arial", 10, "bold"))\
          .grid(row=1, column=0, columnspan=2)
        tk.Label(frame, textvariable=self.sgst_var,
                 font=("Arial", 10, "bold"))\
          .grid(row=1, column=2, columnspan=2)
        tk.Label(frame, textvariable=self.igst_var,
                 font=("Arial", 10, "bold"))\
          .grid(row=2, column=0, columnspan=2)
        tk.Label(frame, textvariable=self.grand_total_var,
                 font=("Arial", 12, "bold"))\
          .grid(row=2, column=2, columnspan=2)

    def add_invoice_row(self):
        self.row_counter += 1
        row_widgets = {}
        r = self.row_counter

        # Serial
        sn = ttk.Entry(self.table_frame, width=5)
        sn.insert(0, str(r)); sn.config(state='readonly')
        sn.grid(row=r, column=0, padx=5, pady=2)
        row_widgets['Serial'] = sn

        # HSN entry
        hsn_var = tk.StringVar()
        hsn_e = ttk.Entry(self.table_frame, textvariable=hsn_var, width=15)
        hsn_e.grid(row=r, column=2, padx=5, pady=2)
        row_widgets['HSN'] = hsn_e

        # Item dropdown (by HSN)
        item_var = tk.StringVar()
        item_dd = ttk.Combobox(self.table_frame, textvariable=item_var,
                               width=37, state="readonly")
        item_dd.grid(row=r, column=1, padx=5, pady=2)
        row_widgets['Item'] = item_dd

        

        def update_items(*_):
            code = hsn_var.get()
            vals = [i for i,c in item_data.items() if c==code]
            item_dd['values'] = vals
            if vals: item_dd.current(0)

        hsn_var.trace_add("write", update_items)

        # Qty, Price, Total
        qty = ttk.Entry(self.table_frame, width=10)
        qty.grid(row=r, column=3, padx=5, pady=2)
        row_widgets['Quantity'] = qty

        pr = ttk.Entry(self.table_frame, width=10)
        pr.grid(row=r, column=4, padx=5, pady=2)
        row_widgets['Price'] = pr

        tot = ttk.Entry(self.table_frame, width=12)
        tot.grid(row=r, column=5, padx=5, pady=2)
        tot.config(state='readonly')
        row_widgets['Total'] = tot

        def calc_tot(*_):
            try:
                q = int(qty.get()); p = float(pr.get())
                val = q*p
                tot.config(state='normal')
                tot.delete(0,'end')
                tot.insert(0,f"{val:.2f}")
                tot.config(state='readonly')
            except: pass

        qty.bind("<FocusOut>", calc_tot)
        pr.bind("<FocusOut>", calc_tot)

        self.invoice_rows.append(row_widgets)

    def calculate_gst_summary(self):
        sub = 0.0
        for w in self.invoice_rows:
            try: sub += int(w['Quantity'].get())*float(w['Price'].get())
            except: pass

        try: rate = float(self.gst_entry.get())
        except: rate=0.0

        if self.txn_type_var.get()=="Intra-state":
            cg = sg = sub*(rate/2)/100
            tot = sub+cg+sg
            self.cgst_var.set(f"CGST: ₹ {cg:.2f}")
            self.sgst_var.set(f"SGST: ₹ {sg:.2f}")
            self.igst_var.set("")
        else:
            ig = sub*rate/100
            tot = sub+ig
            self.igst_var.set(f"IGST: ₹ {ig:.2f}")
            self.cgst_var.set(""); self.sgst_var.set("")

        self.grand_total_var.set(f"Grand Total: ₹ {tot:.2f}")
    def extract_total(self):
        try:
            total_text = self.grand_total_var.get()
            if "₹" in total_text:
                total_text = total_text.split('₹')[-1]
            return float(total_text.strip())
        except:
            return 0.0


    def save_invoice_to_db(self):
        try:
            conn = get_connection()
            cur = conn.cursor()

            invno = INVOICE_FORMAT.format(datetime=datetime.now().strftime("%Y%m%d%H%M%S"))
            today = datetime.today()

            # Save Invoice Header (placeholder - update with your schema)
            cur.execute("""
                INSERT INTO Invoice (InvoiceNumber, Date, BuyerName, BuyerGSTIN, BuyerAddress, BuyerPhone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, invno, today.date(), self.buyer_name.get(), self.buyer_gstin.get(), self.buyer_address.get(), self.buyer_phone.get())

            # Save each item into sales_item table
            for row in self.invoice_rows:
                try:
                    qty = int(row['Quantity'].get())
                    price_ex = float(row['Price'].get())
                    gst_rate = float(self.gst_entry.get())
                    gst_amt = qty * price_ex * gst_rate / 100
                    price_inc = qty * price_ex + gst_amt

                    cur.execute("""
                        INSERT INTO sales_item (InvoiceNumber, InvoiceDate, HSNCode, Quantity,
                            UnitPriceExGST, GSTPercent, GSTAmount, PriceIncGST, ItemDescription)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, invno, today.date(), row['HSN'].get(), qty, price_ex, gst_rate, gst_amt, price_inc, row['Item'].get())
                except Exception as e:
                    print("Skipping row due to error:", e)

            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Invoice and items saved to database!")

        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def search_invoice(self):
        def load_results():
            query = entry.get()
            date_filter = date_entry.get()
            month_filter = month_entry.get()

            sql = "SELECT InvoiceNumber, Date, BuyerName, GrandTotal FROM Invoice WHERE 1=1"
            params = []

            if query:
                sql += " AND (InvoiceNumber LIKE ? OR BuyerName LIKE ?)"
                params.extend((f"%{query}%", f"%{query}%"))
            if date_filter:
                sql += " AND Date = ?"
                params.append(date_filter)
            if month_filter:
                sql += " AND DATENAME(MONTH, Date) = ?"
                params.append(month_filter)

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()

            for row in tree.get_children():
                tree.delete(row)

            for row in rows:
                tree.insert("", "end", values=row)

        win = tk.Toplevel(self.root)
        win.title("Search Invoices")
        win.geometry("700x500")

        tk.Label(win, text="Search by Invoice Number or Buyer Name").pack(pady=2)
        entry = tk.Entry(win, width=50)
        entry.pack(pady=2)

        tk.Label(win, text="Filter by Date (YYYY-MM-DD)").pack(pady=2)
        date_entry = tk.Entry(win, width=20)
        date_entry.pack(pady=2)

        tk.Label(win, text="Filter by Month (e.g., March)").pack(pady=2)
        month_entry = tk.Entry(win, width=20)
        month_entry.pack(pady=2)

        tk.Button(win, text="Search", command=load_results).pack(pady=5)

        tree = ttk.Treeview(win, columns=("InvoiceNumber", "Date", "BuyerName", "GrandTotal"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)



    def export_pdf_styled(self):
        from create_invoice_pdf import create_invoice  # assumed already available

        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not filename:
            return

        today = datetime.today()
        items = []
        for w in self.invoice_rows:
            try:
                q = int(w['Quantity'].get())
                p = float(w['Price'].get())
                tax = q * p * float(self.gst_entry.get()) / 100
                items.append({
                    'description': w['Item'].get(),
                    'hsn': w['HSN'].get(),
                    'qty': q,
                    'unit': "PCS",
                    'rate': p,
                    'tax_percent': float(self.gst_entry.get()),
                    'tax_amount': tax,
                    'amount': q * p
                })
            except:
                pass

        taxable_amount = sum(i['rate'] * i['qty'] for i in items)
        gst_rate = float(self.gst_entry.get())
        txn_type = self.txn_type_var.get()

        totals = {
            'taxable_amount': taxable_amount,
            'total_amount': sum(i['amount'] for i in items)
        }

        if txn_type == 'Inter-state':
            totals['igst_percent'] = gst_rate
            totals['igst_amount'] = taxable_amount * gst_rate / 100
            totals['cgst_percent'] = 0
            totals['cgst_amount'] = 0
            totals['sgst_percent'] = 0
            totals['sgst_amount'] = 0
        else:
            totals['cgst_percent'] = gst_rate / 2
            totals['sgst_percent'] = gst_rate / 2
            totals['cgst_amount'] = taxable_amount * (gst_rate/2) / 100
            totals['sgst_amount'] = taxable_amount * (gst_rate/2) / 100
            totals['igst_percent'] = 0
            totals['igst_amount'] = 0

        data = {
            'company_logo_path': "logo.png",
            'company_name': self.seller_name.get(),
            'company_address': self.seller_address.get(),
            'company_mobile': self.seller_phone.get(),
            'company_gstin': self.seller_gstin.get(),
            'company_pan': "",

            'invoice_no': self.invoice_number.get(),
            'invoice_date': self.invoice_date.get(),
            'due_date': today.strftime("%d/%m/%Y"),

            'customer_name': self.buyer_name.get(),
            'customer_address': self.buyer_address.get(),
            'customer_mobile': self.buyer_phone.get(),
            'customer_gstin': self.buyer_gstin.get(),
            'customer_pan': "",

            'items': items,
            'totals': totals,

            'bank_name_beneficiary': "Deepak Agencies",
            'bank_ifsc': "HDFC0001836",
            'bank_account_no': "50200069375629",
            'bank_name_branch': "HDFC Bank",

            'terms_1': "Goods once sold will not be taken back or exchanged",
            'terms_2': "All disputes are subject to local jurisdiction only",
            'footer_note': "Original for Recipient"
        }

        create_invoice(filename, data)

    def print_transit_copy(self):
        filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                filetypes=[("PDF files","*.pdf")])
        if not filename: return

        today = datetime.today()
        items = []
        for w in self.invoice_rows:
            try:
                q = int(w['Quantity'].get()); p = float(w['Price'].get())
                tax = p*q*float(self.gst_entry.get())/100
                items.append({
                    'description': w['Item'].get(),
                    'hsn': w['HSN'].get(),
                    'qty': q,
                    'unit': "PCS",
                    'rate': p,
                    'tax_percent': float(self.gst_entry.get()),
                    'tax_amount': tax,
                    'amount': p*q+tax
                })
            except: pass

        data = {
            'company_logo_path': "logo.png",
            'company_name': self.seller_name.get(),
            'company_address': self.seller_address.get(),
            'company_mobile': self.seller_phone.get(),
            'company_gstin': self.seller_gstin.get(),
            'company_pan': "",

            'invoice_no': self.invoice_number.get(),
            'invoice_date': self.invoice_date.get(),
            'due_date': today.strftime("%d/%m/%Y"),

            'customer_name': self.buyer_name.get(),
            'customer_address': self.buyer_address.get(),
            'customer_mobile': self.buyer_phone.get(),
            'customer_gstin': self.buyer_gstin.get(),
            'customer_pan': "",

            'items': items,
            'totals': {
                'taxable_amount': sum(i['rate']*i['qty'] for i in items),
                'cgst_percent': float(self.gst_entry.get())/2 if self.txn_type_var.get()=="Intra-state" else 0,
                'cgst_amount': sum(i['rate']*i['qty']*(float(self.gst_entry.get())/2)/100 for i in items),
                'sgst_percent': float(self.gst_entry.get())/2 if self.txn_type_var.get()=="Intra-state" else 0,
                'sgst_amount': sum(i['rate']*i['qty']*(float(self.gst_entry.get())/2)/100 for i in items),
                'total_amount': sum(i['amount'] for i in items)
            },

            'bank_name_beneficiary': BANK_DETAILS['beneficiary'],
            'bank_ifsc': BANK_DETAILS['ifsc'],
            'bank_account_no': BANK_DETAILS['account_no'],
            'bank_name_branch': BANK_DETAILS['bank_branch'],

            'terms_1': "Goods once sold will not be taken back or exchanged",
            'terms_2': "All disputes are subject to local jurisdiction only",
            'footer_note': "Duplicate for Transporter"
        }

        create_invoice(filename, data)



    def lookup_buyer_by_gstin(self, *_):
        gstin = self.buyer_gstin.get().strip()
        if not gstin:
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT BuyerName, BuyerAddress, BuyerPhone FROM client_details WHERE BuyerGSTIN = ?", gstin)
            row = cursor.fetchone()
            conn.close()
            if row:
                self.buyer_name.set(row[0])
                self.buyer_address.set(row[1])
                self.buyer_phone.set(row[2])
        except Exception as e:
            print("Buyer lookup error:", e)


    def save_buyer_to_client_table(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO client_details (BuyerName, BuyerGSTIN, BuyerAddress, BuyerPhone)
                VALUES (?, ?, ?, ?)
            """, self.buyer_name.get(), self.buyer_gstin.get(), self.buyer_address.get(), self.buyer_phone.get())
            conn.commit()
            conn.close()
            messagebox.showinfo("Saved", "Buyer details saved to client_details table.")
        except Exception as e:
            messagebox.showerror("Error", str(e))



    def build_buttons(self):
        frame = tk.Frame(self.root); frame.pack(pady=10)
        ttk.Button(frame, text="Add Row", command=self.add_invoice_row).grid(row=0,column=0,padx=10)
        ttk.Button(frame, text="Calculate GST & Total", command=self.calculate_gst_summary)\
           .grid(row=0,column=1,padx=10)
        ttk.Button(frame, text="Save Invoice to Database", command=self.save_invoice_to_db)\
           .grid(row=0,column=3,padx=10)
        ttk.Button(frame, text="Search Invoices", command=self.search_invoice)\
           .grid(row=0,column=4,padx=10)
        ttk.Button(frame, text="Export Styled PDF", command=self.export_pdf_styled)\
           .grid(row=0,column=5,padx=10)
        ttk.Button(frame, text="Print Transit Copy", command=self.print_transit_copy)\
           .grid(row=0,column=6,padx=10)
        ttk.Button(frame, text="Save Buyer to DB", command=self.save_buyer_to_client_table).grid(row=0, column=7, padx=10)




if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()
