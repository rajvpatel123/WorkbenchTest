import tkinter as tk
from tkinter import ttk, messagebox
import pyvisa

class SpectrumAnalyzerTab:
    def __init__(self, parent, devices):
        self.devices = devices
        self.parent = parent
        self.frame = ttk.Frame(parent)

        self.rm = pyvisa.ResourceManager()
        self.specan = None
        self.connected = False
        self.sweeping = False
        self.armed_and_waiting = False

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

        # Sweep Status LED (top-right)
        self.sweep_led = ttk.Label(self.frame, text="●", font=("Arial", 14), foreground="red")
        self.sweep_led.place(relx=0.97, rely=0.02, anchor='ne')
        self.create_tooltip(self.sweep_led, "Sweep Status: Green = Sweeping, Orange = Armed, Red = Idle")

        # Control Frame
        control_frame = ttk.LabelFrame(self.frame, text="Spectrum Analyzer Controls")
        control_frame.pack(padx=10, pady=10, fill='x')

        # Start / Stop Frequency
        ttk.Label(control_frame, text="Start Frequency (Hz):").grid(row=0, column=0, sticky='w')
        self.start_freq_var = tk.StringVar(value="0")
        ttk.Entry(control_frame, textvariable=self.start_freq_var).grid(row=0, column=1)

        ttk.Label(control_frame, text="Stop Frequency (Hz):").grid(row=1, column=0, sticky='w')
        self.stop_freq_var = tk.StringVar(value="0")
        ttk.Entry(control_frame, textvariable=self.stop_freq_var).grid(row=1, column=1)

        # Reference Level
        ttk.Label(control_frame, text="Reference Level (dBm):").grid(row=2, column=0, sticky='w')
        self.ref_level_var = tk.StringVar(value="0")
        ttk.Entry(control_frame, textvariable=self.ref_level_var).grid(row=2, column=1)

        # RBW
        ttk.Label(control_frame, text="RBW (Hz):").grid(row=3, column=0, sticky='w')
        self.rbw_var = tk.StringVar(value="0")
        ttk.Entry(control_frame, textvariable=self.rbw_var).grid(row=3, column=1)

        # Trigger Mode
        ttk.Label(control_frame, text="Trigger Mode:").grid(row=4, column=0, sticky='w')
        self.trigger_var = tk.StringVar()
        self.trigger_combo = ttk.Combobox(control_frame, textvariable=self.trigger_var, state="readonly")
        self.trigger_combo['values'] = ['Free Run', 'Video', 'External']
        self.trigger_combo.current(0)
        self.trigger_combo.grid(row=4, column=1)

        # Trigger Source
        ttk.Label(control_frame, text="Trigger Source:").grid(row=5, column=0, sticky='w')
        self.trigger_source_var = tk.StringVar()
        self.trigger_source_combo = ttk.Combobox(control_frame, textvariable=self.trigger_source_var, state="readonly")
        self.trigger_source_combo['values'] = ['Signal Gen', 'DAQ', 'Manual']
        self.trigger_source_combo.current(0)
        self.trigger_source_combo.grid(row=5, column=1)

        # Arm and Wait
        self.arm_wait_var = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="Arm and Wait", variable=self.arm_wait_var).grid(row=6, column=1, sticky='w')

        # Sweep Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Start Sweep", command=self.start_sweep).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Stop Sweep", command=self.stop_sweep).pack(side='left', padx=5)

    def connect(self):
        self.specan = self.devices["Spectrum Analyzer"]["instance"]
        if self.specan is None:
            messagebox.showwarning("Not Connected","Please connect via Device Manager Tab")
        else:
            idn = self.specan.query("*IDN?").strip()
            self.status_label.config(text=f"Connected: {idn}", foreground="green")
            self.connected = True

    def start_sweep(self):
        if not self.connected or not self.specan:
            messagebox.showwarning("Not Connected", "Connect to the spectrum analyzer first.")
            return

        try:
            # Apply settings
            self.specan.write(f"FREQ:STAR {self.start_freq_var.get()}")
            self.specan.write(f"FREQ:STOP {self.stop_freq_var.get()}")
            self.specan.write(f"DISP:TRAC:Y:RLEV {self.ref_level_var.get()}")
            self.specan.write(f"BAND:RES {self.rbw_var.get()}")

            trig_mode = self.trigger_var.get()
            if trig_mode == "Free Run":
                self.specan.write("TRIG:SOUR IMM")
            elif trig_mode == "Video":
                self.specan.write("TRIG:SOUR VID")
            elif trig_mode == "External":
                self.specan.write("TRIG:SOUR EXT")

            # Arm and Wait
            if self.arm_wait_var.get():
                self.specan.write("INIT")  # Arm but wait for trigger
                self.armed_and_waiting = True
                self.sweep_led.config(foreground="orange")
            else:
                self.specan.write("INIT:IMM")  # Start immediately
                self.sweeping = True
                self.armed_and_waiting = False
                self.sweep_led.config(foreground="green")

        except Exception as e:
            messagebox.showerror("Sweep Error", str(e))

    def stop_sweep(self):
        if self.specan and self.connected:
            try:
                self.specan.write("ABOR")
                self.sweeping = False
                self.armed_and_waiting = False
                self.sweep_led.config(foreground="red")
            except Exception as e:
                messagebox.showerror("Stop Error", str(e))

    def is_armed_and_waiting(self):
        return self.armed_and_waiting

    def get_trigger_source(self):
        return self.trigger_source_var.get()

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
