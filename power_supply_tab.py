import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyvisa
from psu_driver import (
    AgilentE3648ADriver,
    KeysightU2044XADriver,
    KeysightE36312ADriver,
    KeysightE36232ADriver,
    KeysightE36234ADriver,
)

class CombinedPowerSupplyTab:
    def __init__(self, master, power_supplies, controller):
        self.master = master
        self.power_supplies = power_supplies
        self.controller = controller
        self.frame = ttk.Frame(master)
        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.build_ui()

    def build_ui(self):
        self.output_roles = {}
        self.output_voltages = {}
        self.output_currents = {}

        row = 0
        for psu in self.power_supplies:
            ttk.Label(self.scrollable_frame, text=psu.name, font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=9, sticky="w")
            row += 1
            for i in range(2):
                output_label = f"Output {i+1}"
                ttk.Label(self.scrollable_frame, text=output_label).grid(row=row, column=0, sticky="e")
                volt_entry = ttk.Entry(self.scrollable_frame, width=10)
                volt_entry.grid(row=row, column=1)
                ttk.Label(self.scrollable_frame, text="V").grid(row=row, column=2, sticky="w")

                curr_entry = ttk.Entry(self.scrollable_frame, width=10)
                curr_entry.grid(row=row, column=3)
                ttk.Label(self.scrollable_frame, text="mA").grid(row=row, column=4, sticky="w")

                role = tk.StringVar()
                role.set("None")
                role_menu = ttk.OptionMenu(self.scrollable_frame, role, "None", "Gate", "Drain", "None")
                role_menu.grid(row=row, column=5)

                set_btn = ttk.Button(self.scrollable_frame, text="Set", command=lambda p=psu, ch=i+1: self.set_output(p, ch))
                set_btn.grid(row=row, column=6)

                apply_btn = ttk.Button(self.scrollable_frame, text="Apply", command=lambda p=psu, ch=i+1: self.enable_output(p, ch))
                apply_btn.grid(row=row, column=7)

                disable_btn = ttk.Button(self.scrollable_frame, text="Disable", command=lambda p=psu, ch=i+1: self.disable_output(p, ch))
                disable_btn.grid(row=row, column=8)

                self.output_roles[(psu.name, i+1)] = role
                self.output_voltages[(psu.name, i+1)] = volt_entry
                self.output_currents[(psu.name, i+1)] = curr_entry
                row += 1

            connect_btn = ttk.Button(self.scrollable_frame, text="Connect", command=lambda p=psu: self.connect_psu(p))
            connect_btn.grid(row=row, column=0, columnspan=9, pady=5)
            row += 1

        self.apply_btn = ttk.Button(self.scrollable_frame, text="Apply All", command=self.apply_all)
        self.apply_btn.grid(row=row, column=0, columnspan=9, pady=10)

        self.load_btn = ttk.Button(self.scrollable_frame, text="Load Defaults from File", command=self.load_defaults_from_file)
        self.load_btn.grid(row=row+1, column=0, columnspan=9, pady=5)

    def connect_psu(self, psu):
        try:
            rm = pyvisa.ResourceManager()
            psu.instrument = rm.open_resource(psu.address)
            idn = psu.instrument.query("*IDN?")

            driver_map = {
                "E36484": AgilentE3648ADriver,
                "E3648A": AgilentE3648ADriver,
                "U2044XA": KeysightU2044XADriver,
                "E36312A": KeysightE36312ADriver,
                "E36232A": KeysightE36232ADriver,
                "E36234A": KeysightE36234ADriver,
            }

            matched_driver = None
            for model, driver_cls in driver_map.items():
                if model in idn:
                    matched_driver = driver_cls
                    break

            if not matched_driver:
                raise Exception(f"Unknown PSU model in IDN string: {idn}")

            psu.driver = matched_driver(psu.instrument)
            messagebox.showinfo("Connected", f"{psu.name} connected and driver {matched_driver.__name__} assigned.")

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def set_output(self, psu, channel):
        try:
            v_raw = self.output_voltages[(psu.name, channel)].get()
            c_raw = self.output_currents[(psu.name, channel)].get()
            v = float(v_raw)
            c_mA = float(c_raw)
            c = c_mA / 1000

            if not hasattr(psu, 'driver'):
                raise Exception(f"No driver assigned to {psu.name}")

            psu.driver.set_voltage(channel, v)
            psu.driver.set_current(channel, c)

            key = f"{psu.name} Output{channel}"
            self.controller.output_settings[key] = {
                "voltage": v,
                "current": c
            }

            messagebox.showinfo("Set", f"Set {key} to {v} V / {c} A")

        except Exception as e:
            messagebox.showerror("Set Error", str(e))

    def  (self, psu, channel):
        try:
            if not hasattr(psu, 'driver'):
                raise Exception(f"No driver assigned to {psu.name}")

            voltage = float(voltage_entry.get())
            milliamps = float(current_entry.get())
            current = milliamps / 1000.0  # Convert mA to A
            key = f"{psu_name} {output_name}"

            self.output_settings[key] = {"voltage": voltage, "current": current}
            print(f"[{key}] V={voltage}V, I={current}A (from {milliamps}mA)")

            self.psu_supplies[psu_name].set_voltage(output_name, voltage)
            self.psu_supplies[psu_name].set_current(output_name, current)
            messagebox.showinfo("Output Enabled", f"{psu.name} Output {channel} is now ON")

        except Exception as e:
            messagebox.showerror("Enable Error", str(e))

    def disable_output(self, psu, channel):
        try:
            if not hasattr(psu, 'driver'):
                raise Exception(f"No driver assigned to {psu.name}")

            psu.driver.disable_output(channel)
            messagebox.showinfo("Output Disabled", f"{psu.name} Output {channel} is now OFF")

        except Exception as e:
            messagebox.showerror("Disable Error", str(e))

    def apply_all(self):
        for psu in self.power_supplies:
            for i in range(2):
                try:
                    self.set_output(psu, i+1)
                    self.enable_output(psu, i+1)
                except Exception as e:
                    print(f"Failed to apply settings for {psu.name} Output {i+1}: {e}")


    def apply_bias_settings(self, cfg):

        try:
            for psu in self.power_supplies:  # assume self.power_supplies is a list of PSU objects
                for output in psu.outputs:
                    if output.role == 'Gate':
                        voltage = cfg.get("VGDRV", 0)
                        current = cfg.get("IDDRV", 0)
                    elif output.role == 'Drain':
                        voltage = cfg.get("VDDRV", 0)
                        current = cfg.get("IDDRV", 0)
                    else:
                        continue  # skip if role is unassigned
                    output.set_voltage(voltage)
                    output.set_current(current)
        except Exception as e:
            print(f"⚠️ PSU Config Error: {e}")
    def load_defaults_from_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filepath:
            return
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            for line in lines:
                parts = line.strip().split("_")
                if len(parts) == 3:
                    psu, output, role = parts
                    output_num = 1 if output.lower() == "output1" else 2
                    key = (psu, output_num)
                    if key in self.output_roles:
                        self.output_roles[key].set(role)
        except Exception as e:
            messagebox.showerror("File Error", str(e))
