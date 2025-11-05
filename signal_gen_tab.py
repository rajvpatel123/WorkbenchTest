import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyvisa
import os
import ntpath

class SignalGeneratorTab:
    def __init__(self, parent, devices):
        self.devices = devices
        self.parent = parent
        self.frame = ttk.Frame(parent)

        self.rm = pyvisa.ResourceManager()
        self.siggen = None
        self.connected = False

        self.build_ui()

    def build_ui(self):
        # Connection Frame
        conn_frame = ttk.LabelFrame(self.frame, text="Connection")
        conn_frame.pack(padx=10, pady=10, fill='x')

        self.visa_resource_var = tk.StringVar()
        self.resource_entry = ttk.Entry(conn_frame, textvariable=self.visa_resource_var, width=40)
        self.resource_entry.pack(side='left', padx=5)

        ttk.Button(conn_frame, text="Connect", command=self.connect).pack(side='left', padx=5)
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side='left', padx=5)

        # RF Output LED Indicator (top-right corner)
        self.rf_status_led = ttk.Label(self.frame, text="●", font=("Arial", 14), foreground="red")
        self.rf_status_led.place(relx=0.97, rely=0.02, anchor='ne')
        self.create_tooltip(self.rf_status_led, "RF Output Status: Green = ON, Red = OFF")

        # Controls Frame
        control_frame = ttk.LabelFrame(self.frame, text="Signal Generator Controls")
        control_frame.pack(padx=10, pady=10, fill='x')

        # Frequency with unit selection
        ttk.Label(control_frame, text="Frequency:").grid(row=0, column=0, sticky='w')
        self.freq_val_var = tk.StringVar(value="0")
        ttk.Entry(control_frame, textvariable=self.freq_val_var, width=10).grid(row=0, column=1, sticky='w')

        self.freq_unit_var = tk.StringVar(value="Hz")
        unit_frame = ttk.Frame(control_frame)
        unit_frame.grid(row=0, column=2, sticky='w')
        ttk.Radiobutton(unit_frame, text="Hz", variable=self.freq_unit_var, value="Hz").pack(side='left')
        ttk.Radiobutton(unit_frame, text="kHz", variable=self.freq_unit_var, value="kHz").pack(side='left')
        ttk.Radiobutton(unit_frame, text="GHz", variable=self.freq_unit_var, value="GHz").pack(side='left')

        # Power
        ttk.Label(control_frame, text="Power (dBm):").grid(row=1, column=0, sticky='w')
        self.power_var = tk.StringVar(value="0")
        ttk.Entry(control_frame, textvariable=self.power_var).grid(row=1, column=1)

        # Waveform Dropdown
        ttk.Label(control_frame, text="Waveform:").grid(row=2, column=0, sticky='w')
        self.waveform_var = tk.StringVar()
        self.waveform_combo = ttk.Combobox(control_frame, textvariable=self.waveform_var, state="readonly")
        self.waveform_combo['values'] = ['SIN', 'SQU', 'PULS', 'RAMP', 'NOIS', 'Choose My Own']
        self.waveform_combo.current(0)
        self.waveform_combo.grid(row=2, column=1)
        self.waveform_combo.bind("<<ComboboxSelected>>", self.on_waveform_change)

        # File picker for custom waveform
        self.arb_file_var = tk.StringVar()
        self.arb_file_entry = ttk.Entry(control_frame, textvariable=self.arb_file_var, width=30)
        self.arb_file_button = ttk.Button(control_frame, text="Browse...", command=self.browse_arb_file)
        self.arb_file_entry.grid(row=3, column=0, columnspan=2, pady=(5, 0))
        self.arb_file_button.grid(row=3, column=2, padx=(5, 0))
        self.arb_file_entry.grid_remove()
        self.arb_file_button.grid_remove()
 
        # Playback Mode
        ttk.Label(control_frame, text="Playback Mode:").grid(row=4, column=0, sticky='w')
        self.repeat_mode_var = tk.StringVar(value="Repeat")
        repeat_frame = ttk.Frame(control_frame)
        repeat_frame.grid(row=4, column=1, sticky='w')
        ttk.Radiobutton(repeat_frame, text="Repeat", variable=self.repeat_mode_var, value="Repeat").pack(side='left')
        ttk.Radiobutton(repeat_frame, text="Play Once", variable=self.repeat_mode_var, value="Play Once").pack(side='left')

        # RF Output Toggle
        self.output_state = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="RF Output ON", variable=self.output_state).grid(row=5, column=1, sticky='w')

        # Apply Button
        ttk.Button(control_frame, text="Apply Settings", command=self.apply_settings).grid(row=6, column=0, columnspan=3, pady=10)

        # List Available ARB Waveforms
        ttk.Button(control_frame, text="List ARB Waveforms", command=self.list_waveforms).grid(row=7, column=0, pady=5)

        self.arb_listbox = tk.Listbox(control_frame, height=5, width=40)
        self.arb_listbox.grid(row=8, column=0, columnspan=3, padx=5, pady=(0, 5))

        # Load Selected ARB Button
        ttk.Button(control_frame, text="Load Selected ARB", command=self.load_selected_waveform).grid(row=9, column=0, columnspan=3, pady=(0, 10))

    def connect(self):
        self.siggen = self.devices["Signal Generator"]["instance"]
        if self.siggen is None:
            messagebox.showwarning("Not Connected","Please connect via Device Manager Tab")
        else:
            idn = self.siggen.query("*IDN?").strip()
            self.status_label.config(text=f"Connected: {idn}", foreground="green")
            self.connected = True

    def on_waveform_change(self, event=None):
        if self.waveform_var.get() == "Choose My Own":
            self.arb_file_entry.grid()
            self.arb_file_button.grid()
        else:
            self.arb_file_entry.grid_remove()
            self.arb_file_button.grid_remove()

    def browse_arb_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Waveform Files", "*.wv *.csv *.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.arb_file_var.set(file_path)

    def apply_settings(self):
        if not self.connected or not self.siggen:
            messagebox.showwarning("Not Connected", "Connect to the signal generator first.")
            return

        try:
            freq_val = float(self.freq_val_var.get())
            unit = self.freq_unit_var.get()
            multiplier = {"Hz": 1, "kHz": 1e3, "GHz": 1e9}[unit]
            freq = freq_val * multiplier

            power = float(self.power_var.get())
            wave = self.waveform_var.get()
            rf_on = self.output_state.get()

            self.siggen.write(f"FREQ {freq}")
            self.siggen.write(f"POW {power}")

            if wave == "Choose My Own":
                filepath = self.arb_file_var.get()
                if not filepath:
                    messagebox.showwarning("Missing File", "Please select a waveform file.")
                    return

                try:
                    filename = ntpath.basename(filepath)
                    arb_name = "WAVE1"

                    with open(filepath, 'rb') as f:
                        file_contents = f.read()

                    header = f"MMEM:DATA:LOAD '{arb_name}',#{len(str(len(file_contents)))}{len(file_contents)}"
                    self.siggen.write_raw(header.encode('ascii') + file_contents)

                    self.siggen.write(f"SOUR:ARB:WAV '{arb_name}'")
                    self.siggen.write("SOUR:FUNC ARB")

                    repeat_mode = self.repeat_mode_var.get()
                    self.siggen.write("SOUR:ARB:REP ON" if repeat_mode == "Repeat" else "SOUR:ARB:REP OFF")

                except Exception as e:
                    messagebox.showerror("ARB Upload Failed", str(e))
                    return
            else:
                self.siggen.write(f"FUNC {wave}")

            self.siggen.write("OUTP ON" if rf_on else "OUTP OFF")
            self.rf_status_led.config(foreground="green" if rf_on else "red")

            messagebox.showinfo("Success", "Settings applied successfully.")
        except Exception as e:
            messagebox.showerror("Command Error", str(e))

    def list_waveforms(self):
        if not self.connected or not self.siggen:
            messagebox.showwarning("Not Connected", "Connect to the signal generator first.")
            return

        try:
            self.siggen.write("MMEM:CD '/var/user/Waveforms'")
            response = self.siggen.query(f'MMEM:CAT? "/var/user/Waveforms"')
            files = response.strip().split(',')

            self.arb_listbox.delete(0, tk.END)
            for i in range(0, len(files), 2):
                filename = files[i].strip().strip('"')
                if filename.lower().endswith(('.wv', '.csv', '.txt')):
                    self.arb_listbox.insert(tk.END, filename)

            if self.arb_listbox.size() == 0:
                self.arb_listbox.insert(tk.END, "No ARB files found.")

        except Exception as e:
            messagebox.showerror("Error Listing Files", str(e))

    def load_selected_waveform(self):
        if not self.connected or not self.siggen:
            messagebox.showwarning("Not Connected", "Connect to the signal generator first.")
            return

        try:
            selected = self.arb_listbox.get(tk.ACTIVE)
            if not selected or selected.startswith("No ARB"):
                return

            self.siggen.write(f"SOUR:ARB:WAV '{selected}'")
            self.siggen.write("SOUR:FUNC ARB")

            repeat_mode = self.repeat_mode_var.get()
            self.siggen.write("SOUR:ARB:REP ON" if repeat_mode == "Repeat" else "SOUR:ARB:REP OFF")

            messagebox.showinfo("ARB Loaded", f"Waveform '{selected}' is now active.")

        except Exception as e:
            messagebox.showerror("Load Failed", str(e))

    def configure_from_setup(self, cfg):

        try:
            start_freq = cfg.get("LOSWPFREQMZ", 1000) * 1e6  # MHz to Hz
            stop_freq = cfg.get("HISWPFREQMZ", 2000) * 1e6
            power = cfg.get("LOSWPPWR", 10)  # dBm 

            self.set_frequency(start_freq)
            self.set_power(power)
            self.set_arb_waveform("default_waveform")  # or use file selection
        except Exception as e:
            print(f"⚠️ Signal Gen Config Error: {e}")
            
    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        label = tk.Label(tooltip, text=text, background="yellow", relief='solid', borderwidth=1, font=("Arial", 9))
        label.pack()

        def show(event):
            tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip.deiconify()

        def hide(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def get_tab(self):
        return self.frame

