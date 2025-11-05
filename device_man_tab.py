import tkinter as tk
from tkinter import ttk, messagebox
import pyvisa

class DeviceManagerTab:
    def __init__(self, root, devices):
        self.root = root
        self.frame = ttk.Frame(root)
        self.devices = devices  # Dictionary: name -> {'address': str, 'instance': object}
        self.rm = pyvisa.ResourceManager()
        self.status_vars = {}  # name -> tk.StringVar

        self.build_ui()

    def build_ui(self):
        # Connect All button
        ttk.Button(self.frame, text="🔗 Connect All Devices", command=self.connect_all).pack(pady=10)

        # Device list
        self.tree = ttk.Treeview(self.frame, columns=("Device", "Status", "Action"), show="headings")
        self.tree.heading("Device", text="Device")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Action", text="")
        self.tree.column("Device", width=200)
        self.tree.column("Status", width=300)
        self.tree.column("Action", width=100)
        self.tree.pack(padx=10, pady=5, fill='both', expand=True)

        for name in self.devices:
            self.status_vars[name] = tk.StringVar(value="❌ Not Connected")
            self.tree.insert("", "end", iid=name, values=(
                self.devices[name]['user'],
                self.status_vars[name].get(),
                "Ready to Connect"
            ))

        self.tree.bind("<Double-1>", self.on_tree_double_click)

    def on_tree_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.connect_device(item)

    def connect_device(self, name):
        try:
            address = self.devices[name]['address']
            instrument = self.rm.open_resource(address)
            idn = instrument.query("*IDN?").strip()
            self.devices[name]['instance'] = instrument
            self.status_vars[name].set(f"✅ Connected: {idn}")
            self.tree.item(name, values=(address, self.status_vars[name].get(), "Reconnect"))
        except Exception as e:
            self.status_vars[name].set("❌ Connection Failed")
            self.tree.item(name, values=(address, self.status_vars[name].get(), "Retry"))
            messagebox.showerror(f"{name} Connection Error", str(e))

    def connect_all(self):
        for name in self.devices:
            self.connect_device(name)

    def get_tab(self):
        return self.frame

    
    
    

