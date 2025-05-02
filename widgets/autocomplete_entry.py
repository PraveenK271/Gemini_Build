import tkinter as tk
from tkinter import ttk

class AutocompleteEntry(ttk.Entry):
    def __init__(self, autocomplete_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.autocomplete_list = autocomplete_list
        self.var = self["textvariable"] = tk.StringVar()
        self.var.trace_add("write", self.on_change)
        self.bind("<Right>", self.select_suggestion)
        self.lb = None

    def on_change(self, *args):
        pattern = self.var.get().lower()
        matches = [x for x in self.autocomplete_list if pattern in x.lower()]
    
        if matches:
            if not self.lb:
                self.lb = tk.Listbox(self.master, width=self["width"])
                self.lb.bind("<<ListboxSelect>>", self.select_item)
        
            # Calculate screen-relative position
            x = self.winfo_rootx() - self.master.winfo_rootx()
            y = self.winfo_y() + self.winfo_height()
            self.lb.place(in_=self.master, x=x, y=y)

            self.lb.delete(0, tk.END)
            for item in matches:
                self.lb.insert(tk.END, item)
        else:
            if self.lb:
                self.lb.destroy()
                self.lb = None


    def select_item(self, event):
        if self.lb:
            selection = self.lb.get(self.lb.curselection())
            self.var.set(selection)
            self.lb.destroy()
            self.lb = None

    def select_suggestion(self, event):
        if self.lb and self.lb.size() > 0:
            self.var.set(self.lb.get(0))
            self.lb.destroy()
            self.lb = None
