import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyvisa
import time
from pairing_tab import PairingTab
from signal_gen_tab import SignalGeneratorTab
from spectrum_analyzer_tab import SpectrumAnalyzerTab
from power_supply import PowerSupply
from power_supply_tab import CombinedPowerSupplyTab
from device_man_tab import DeviceManagerTab
from test_seq_tab import TestSequencerTab

class App:
# Function: __init__
    def __init__(self, root):
        self.root = root
        self.root.title("Workbench Automation GUI")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")
        self.output_settings = {}  # Store voltage and current settings per output
        
        self.assignment_data = [
        {'psu': 'PS1', 'output': 'Output1', 'role' : 'Gate'},
        {'psu': 'PS1', 'output': 'Output2', 'role' : 'Gate'},
        {'psu': 'PS2', 'output': 'Output1', 'role' : 'Gate'},
        {'psu': 'PS2', 'output': 'Output2', 'role' : 'Drain'},
        {'psu': 'PS3', 'output': 'Output1', 'role' : 'Gate'},
        {'psu': 'PS3', 'output': 'Output2', 'role' : 'Gate'},
        {'psu': 'PS4', 'output': 'Output1', 'role' : 'Drain'},
        {'psu': 'PS4', 'output': 'Output2', 'role' : 'Drain'},
        
        ]

        self.power_supplies = [
            PowerSupply("PS1", "GPIB0::10::INSTR"),
            PowerSupply("PS2", "GPIB0::11::INSTR"),
            PowerSupply("PS3", "GPIB0::15::INSTR"),
            PowerSupply("PS4", "USB0::0x2A8D::0x3402::MY61002290::INSTR"),
        ]
        
            
    
    
        self.devices = {
            "PSU1": {"address": "GPIB0::10::INSTR", "instance": None, "user":"PS1"},
            "PSU2": {"address": "GPIB0::11::INSTR", "instance": None, "user":"PS2"},
            "PSU3": {"address": "GPIB0::15::INSTR", "instance": None, "user":"PS3"},
            "PSU4": {"address": "USB0::0x2A8D::0x3402::MY61002290::INSTR", "instance": None, "user":"PS4"},
            "Signal Generator": {"address": "GPIB0::28::INSTR", "instance": None, "user":"Signal Generator"},
            "Spectrum Analyzer": {"address": "GPIB0::18::INSTR", "instance": None, "user":"Spectrum Analyzer"},
        }


        self.device_tab = DeviceManagerTab(self.root, self.devices)
        self.notebook.add(self.device_tab.get_tab(), text="Device Manager")

        self.ps_tab = CombinedPowerSupplyTab(self.notebook, self.power_supplies, controller = self)
# Add new tab to the notebook
        self.notebook.add(self.ps_tab.frame, text="Power Supplies")
        
        self.pairing_tab = PairingTab(self.notebook, self.assignment_data, controller =self)
# Add new tab to the notebook
        self.notebook.add(self.pairing_tab.frame, text = "Pairing G/D")

        self.sg_tab = SignalGeneratorTab(self.notebook, self.devices)
# Add new tab to the notebook
        self.notebook.add(self.sg_tab.frame, text="Signal Generator")

        self.sa_tab = SpectrumAnalyzerTab(self.notebook, self.devices )
# Add new tab to the notebook
        self.notebook.add(self.sa_tab.frame, text="Spectrum Analyzer")
        
        self.seq_tab = TestSequencerTab(self.notebook, self.devices, self.ps_tab, self.sg_tab, self.sa_tab)
        self.notebook.add(self.seq_tab.get_tab(), text = "Test Sequencer")
        


    def apply_output(self, psu_name, output_name, voltage_entry, current_entry):
        try:
            voltage = float(voltage_entry.get())
            milliamps = float(current_entry.get())
            current = milliamps / 1000.0  # Convert mA to A
            key = f"{psu_name} {output_name}"

            self.output_settings[key] = {"voltage": voltage, "current": current}
            print(f"[{key}] V={voltage}V, I={current}A (from {milliamps}mA)")

            self.psu_supplies[psu_name].set_voltage(output_name, voltage)
            self.psu_supplies[psu_name].set_current(output_name, current)

        except Exception as e:
            messagebox.showerror("Apply Failed", f"Could not apply settings for {psu_name} {output_name}\n{e}")
