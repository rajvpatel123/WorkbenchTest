import tkinter as tk
from tkinter import ttk, messagebox
import time


class PairingTab:
    def __init__(self, parent, assignments, controller):
        self.controller = controller
        self.assignments = assignments
        self.pairings = []
        self.frame = ttk.Frame(parent)

        self.gates = [a for a in assignments if a['role'].lower() == 'gate']
        self.drains = [a for a in assignments if a['role'].lower() == 'drain']

        self.selected_gates = {}
        self.selected_drains = {}

        self.activate_button = ttk.Button(self.frame, text="Activate Pairs", command=self.activate_all_pairs)
        self.activate_button.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(self.frame, text="Deactivate All Pairs", command=self.deactivate_all_pairs).grid(row=6, column=0, columnspan=2, pady=5)

        ttk.Label(self.frame, text="Gate Outputs").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.gate_frame = ttk.Frame(self.frame)
        self.gate_frame.grid(row=1, column=0, padx=10, sticky="nw")

        ttk.Label(self.frame, text="Drain Outputs").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.drain_frame = ttk.Frame(self.frame)
        self.drain_frame.grid(row=1, column=1, padx=10, sticky="nw")

        self.populate_checkboxes()

        self.pair_button = ttk.Button(self.frame, text="Pair Selected", command=self.pair_selected)
        self.pair_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.unpair_button = ttk.Button(self.frame, text="Unpair Selected", command=self.unpair_selected)
        self.unpair_button.grid(row=2, column=1, columnspan=2, pady=10)

        ttk.Label(self.frame, text="Paired Outputs:").grid(row=3, column=0, columnspan=2, sticky="w", padx=10)
        self.pair_listbox = tk.Listbox(self.frame, height=10, width=65)
        self.pair_listbox.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

    def make_gate_callback(self, var, key):
        def callback():
            if var.get():
                for other_key, (other_var, _) in self.selected_gates.items():
                    if other_key != key:
                        other_var.set(False)
        return callback

    def make_drain_callback(self, var, key):
        def callback():
            if var.get():
                for other_key, (other_var, _) in self.selected_drains.items():
                    if other_key != key:
                        other_var.set(False)
        return callback

    def populate_checkboxes(self):
        for widget in self.gate_frame.winfo_children():
            widget.destroy()
        for widget in self.drain_frame.winfo_children():
            widget.destroy()

        self.selected_gates.clear()
        self.selected_drains.clear()

        for gate in self.gates:
            key = f"{gate['psu']} {gate['output']}"
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.gate_frame, text=key, variable=var, command=self.make_gate_callback(var, key))
            chk.pack(anchor='w')
            self.selected_gates[key] = (var, gate)

        for drain in self.drains:
            key = f"{drain['psu']} {drain['output']}"
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.drain_frame, text=key, variable=var, command=self.make_drain_callback(var, key))
            chk.pack(anchor='w')
            self.selected_drains[key] = (var, drain)

    def pair_selected(self):
        selected_gate = [gate for key, (var, gate) in self.selected_gates.items() if var.get()]
        selected_drain = [drain for key, (var, drain) in self.selected_drains.items() if var.get()]

        if len(selected_gate) != 1 or len(selected_drain) != 1:
            messagebox.showerror("Selection Error", "Please select exactly one gate and one drain.")
            return

        gate = selected_gate[0]
        drain = selected_drain[0]

        if (gate, drain) in self.pairings:
            messagebox.showinfo("Already Paired", "This pair has already been created.")
            return

        self.pairings.append((gate, drain))
        self.pair_listbox.insert(tk.END, f"[ ] {gate['psu']} {gate['output']} ⟶ {drain['psu']} {drain['output']}")
        self.gates.remove(gate)
        self.drains.remove(drain)
        self.populate_checkboxes()

    def unpair_selected(self):
        selection = self.pair_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        pair_text = self.pair_listbox.get(index)

        for i, (gate, drain) in enumerate(self.pairings):
            expected_text = f"{gate['psu']} {gate['output']} ⟶ {drain['psu']} {drain['output']}"
            if expected_text in pair_text:
                self.gates.append(gate)
                self.drains.append(drain)
                self.pairings.pop(i)
                self.pair_listbox.delete(index)
                self.populate_checkboxes()
                return

    def ramp_voltage(self, psu, output, sequence):
        for voltage, current, delay in sequence:
            print(f"[DEBUG] Applying to {psu.name} output {output}: {voltage}V @ {current}A (delay {delay}s)")
            psu.driver.apply_output(output, voltage, current)
            time.sleep(delay)

    def activate_all_pairs(self):
        for i, (gate, drain) in enumerate(self.pairings):
            gate_key = f"{gate['psu']} {gate['output']}"
            drain_key = f"{drain['psu']} {drain['output']}"

            gate_settings = self.controller.output_settings.get(gate_key)
            drain_settings = self.controller.output_settings.get(drain_key)

            if not gate_settings or not drain_settings:
                error_msg = f"[X] Missing settings for {gate_key} or {drain_key}"
                self.pair_listbox.insert(tk.END, error_msg)
                continue

            gate_psu = self.controller.psu_supplies[gate['psu']]
            drain_psu = self.controller.psu_supplies[drain['psu']]
            gate_output = gate['output']
            drain_output = drain['output']

            try:
                self.ramp_voltage(gate_psu, gate_output, [(-6.0, gate_settings['current'], 0.5)])
                self.ramp_voltage(drain_psu, drain_output, [
                    (0.0, drain_settings['current'], 0.5),
                    (10.0, drain_settings['current'], 0.5),
                    (drain_settings['voltage'], drain_settings['current'], 0.5)
                ])
                self.ramp_voltage(gate_psu, gate_output, [
                    (-3.0, gate_settings['current'], 0.5),
                    (gate_settings['voltage'], gate_settings['current'], 0.0)
                ])

                line = self.pair_listbox.get(i)
                self.pair_listbox.delete(i)
                self.pair_listbox.insert(i, line.replace("[ ]", "[✓]"))

            except Exception as e:
                self.pair_listbox.insert(tk.END, f"[X] Activation failed: {gate_key} -> {drain_key}: {str(e)}")

    def deactivate_all_pairs(self):
        for gate, drain in self.pairings:
            gate_key = f"{gate['psu']} {gate['output']}"
            drain_key = f"{drain['psu']} {drain['output']}"

            gate_settings = self.controller.output_settings.get(gate_key)
            drain_settings = self.controller.output_settings.get(drain_key)

            gate_psu = self.controller.psu_controllers[gate['psu']]
            drain_psu = self.controller.psu_controllers[drain['psu']]
            gate_output = gate['output']
            drain_output = drain['output']

            try:
                self.ramp_voltage(gate_psu, gate_output, [
                    (-3.0, gate_settings['current'], 0.5),
                    (-6.0, gate_settings['current'], 0.5)
                ])
                self.ramp_voltage(drain_psu, drain_output, [
                    (10.0, drain_settings['current'], 0.5),
                    (0.0, drain_settings['current'], 0.0)
                ])
            except Exception as e:
                self.pair_listbox.insert(tk.END, f"[X] Deactivation failed: {gate_key} -> {drain_key}: {str(e)}")

