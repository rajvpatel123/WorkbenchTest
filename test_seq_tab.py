import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time

class TestSequencerTab:
    def __init__(self, parent, devices, psu_controller, siggen_controller, specan_controller):
        self.parent = parent
        self.devices = devices
        self.psus = psu_controller
        self.siggen = siggen_controller
        self.specan = specan_controller

        self.running = False
        self.delay_units = {}  # step -> 's' or 'ms'
        self.delay_values = {}  # step -> float
        self.test_config = {}  # parsed test setup file values
        self.config_vars = {}  # tk.StringVar for display

        self.frame = ttk.Frame(self.parent)
        self.build_ui()

    def build_ui(self):
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(pady=10, padx=10, fill='x')

        self.run_button = ttk.Button(control_frame, text="▶ Run Test Sequence", command=self.run_sequence)
        self.run_button.pack(side='left', padx=5)

        self.stop_button = ttk.Button(control_frame, text="🛑 Stop", command=self.stop_sequence)
        self.stop_button.pack(side='left', padx=5)

        self.status_label = ttk.Label(control_frame, text="Idle", foreground="gray")
        self.status_label.pack(side='right', padx=10)

        delay_frame = ttk.LabelFrame(self.frame, text="Step Delays")
        delay_frame.pack(padx=10, pady=5, fill='x')

        self.step_names = ["Bias ON", "RF ON", "Sweep", "Log", "RF OFF", "Bias OFF"]
        for step in self.step_names:
            row = ttk.Frame(delay_frame)
            row.pack(fill='x', padx=5, pady=2)
            ttk.Label(row, text=step, width=12).pack(side='left')

            val = tk.DoubleVar(value=1.0)
            self.delay_values[step] = val
            ttk.Entry(row, textvariable=val, width=6).pack(side='left')

            unit = tk.StringVar(value='s')
            self.delay_units[step] = unit
            ttk.Radiobutton(row, text="sec", variable=unit, value='s').pack(side='left')
            ttk.Radiobutton(row, text="ms", variable=unit, value='ms').pack(side='left')

        config_frame = ttk.LabelFrame(self.frame, text="Test Setup File")
        config_frame.pack(padx=10, pady=5, fill='both')

        load_btn = ttk.Button(config_frame, text="📂 Load Setup File", command=self.load_setup_file)
        load_btn.pack(anchor='w', padx=5, pady=5)

        self.config_display = tk.Text(config_frame, height=12, width=60, state='disabled', background="#f9f9f9")
        self.config_display.pack(padx=5, pady=5)

        self.steps_box = tk.Text(self.frame, height=10, width=60, state='disabled', background="#f4f4f4")
        self.steps_box.pack(pady=5, padx=10)

    def load_setup_file(self):
        file_path = filedialog.askopenfilename(title="Select Setup File", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            self.test_config.clear()
            for line in lines:
                if '=' in line:
                    key, value = line.strip().split('=')
                    self.test_config[key] = float(value)

            self.config_display.config(state='normal')
            self.config_display.delete("1.0", tk.END)
            for k, v in self.test_config.items():
                self.config_display.insert(tk.END, f"{k} = {v}\n")
            self.config_display.config(state='disabled')
            self.log_step(f"✅ Loaded setup file: {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load setup file:\n{str(e)}")

    def log_step(self, message):
        self.steps_box.config(state='normal')
        self.steps_box.insert(tk.END, f"{message}\n")
        self.steps_box.see(tk.END)
        self.steps_box.config(state='disabled')

    def set_status(self, text, color="blue"):
        self.status_label.config(text=text, foreground=color)
        self.status_label.update()

    def run_sequence(self):
        if self.running:
            return
        self.running = True
        self.set_status("Running...", "green")
        self.steps_box.config(state='normal')
        self.steps_box.delete("1.0", tk.END)
        self.steps_box.config(state='disabled')

        thread = threading.Thread(target=self._run_test_flow)
        thread.start()

    def stop_sequence(self):
        if self.running:
            self.running = False
            self.set_status("Stopping...", "orange")

    def get_delay(self, step):
        val = self.delay_values[step].get()
        unit = self.delay_units[step].get()
        return val / 1000 if unit == 'ms' else val

    def _run_test_flow(self):
        try:
            cfg = self.test_config

            # Step 1: Bias ON
            if not self.running: return
            self.log_step("Step 1: Bias ON")
            self.set_status("Biasing...")
            if cfg:
                self.psus.apply_bias_settings(cfg)
            self.psus.apply_all()
            time.sleep(self.get_delay("Bias ON"))

            # Step 2: RF ON
            if not self.running: return
            self.log_step("Step 2: RF ON")
            self.set_status("Enabling RF...")
            if cfg:
                self.siggen.configure_from_setup(cfg)
            self.siggen.apply_settings()
            time.sleep(self.get_delay("RF ON"))

            # Step 3: Sweep
            if not self.running: return
            self.log_step("Step 3: Triggering Spectrum Analyzer Sweep")
            self.set_status("Triggering Sweep...")
            self.specan.start_sweep()
            time.sleep(self.get_delay("Sweep"))

            # Step 4: Log Data (placeholder)
            if not self.running: return
            self.log_step("Step 4: Logging Data")
            self.set_status("Logging...")
            # [Add logging logic here]
            time.sleep(self.get_delay("Log"))

            # Step 5: RF OFF
            if not self.running: return
            self.log_step("Step 5: RF OFF")
            self.set_status("Disabling RF...")
            self.siggen.apply_settings()
            time.sleep(self.get_delay("RF OFF"))

            # Step 6: Bias OFF
            if not self.running: return
            self.log_step("Step 6: Bias OFF")
            self.set_status("Powering Down...")
            self.psus.apply_all()
            time.sleep(self.get_delay("Bias OFF"))

            self.set_status("Complete", "green")
            self.log_step("✅ Test Complete")

        except Exception as e:
            self.set_status("Error", "red")
            self.log_step(f"❌ Error: {str(e)}")
        finally:
            self.running = False

    def get_tab(self):
        return self.frame

