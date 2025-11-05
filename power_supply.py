import tkinter as tk
from tkinter import ttk
import pyvisa

class PowerSupply:
    def __init__(self, name, address):
        self.name = name
        self.address = address
        self.instrument = None
        