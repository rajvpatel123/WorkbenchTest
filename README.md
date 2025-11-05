WorkbenchTest — NI-MAX-like RF/Lab Test Bench (Python)
======================================================

Python GUI for discovering, configuring, and controlling lab instruments
(PSUs, Signal Generator, Spectrum Analyzer, etc.) over VISA/SCPI. Tabs include
Device Manager, Power Supplies, Signal Generator, Spectrum Analyzer, Pairing (Gate/Drain),
and a Test Sequencer—with safety-first ramp logic and trigger handshakes.

Features
--------
- Device Manager (device_man_tab.py): Enumerates VISA resources, shows IDNs, and centralizes connect/disconnect.
- Power Supplies (power_supply_tab.py, power_supply.py, psu_driver.py):
  - Two outputs per PSU (Out1/Out2) with Gate/Drain roles, V/I setpoints, readback, enable/disable
  - Safe ramp up/down sequences with multi-step logic
- Signal Generator (signal_gen_tab.py):
  - Frequency with Hz/kHz/GHz unit radio buttons
  - RF on/off, level control, ARB repeat/once toggle
- Spectrum Analyzer (spectrum_analyzer_tab.py):
  - Trigger Source: Signal Gen / DAQ / Manual
  - Arm & Wait; PSU ramp can wait until analyzer is ready
- Pairing Tab (pairing_tab.py):
  - Load role/label file and enforce one-to-one Gate↔Drain mapping across PSUs
- Test Sequencer (test_seq_tab.py):
  - Recipe: Bias ON → RF ON → Sweep → Log → RF OFF → Bias OFF
  - Per-step delays in s/ms; integrates trigger/arm logic
- App Controller / Entry (app_controller.py, main.py):
  - High-level orchestration and application bootstrap

Tech & Dependencies
-------------------
- Python 3.11+ (tested on 3.12/3.13)
- GUI: PySide6 (or PyQt6 if preferred)
- I/O: pyvisa, a VISA backend (NI-VISA or Keysight IO Libraries)
- Optional: matplotlib, loguru
Suggested requirements.txt:
  pyvisa>=1.13
  PySide6>=6.6
  loguru>=0.7
  matplotlib>=3.8
  python-dotenv>=1.0

Installation
------------
1) System prerequisites
   - Install one VISA stack (pick one):
     * NI-VISA (NI) OR
     * Keysight IO Libraries Suite
   - Optional: GPIB drivers (NI-488.2/Keysight) if using GPIB.

2) Clone & set up environment
   git clone https://github.com/rajvpatel123/WorkbenchTest.git
   cd WorkbenchTest
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate

   pip install -U pip
   pip install -r requirements.txt

Configuration
-------------
Create a .env in the project root:

  VISA_BACKEND=ni           # "ni" or "keysight"; optional
  PSU1_ADDR=GPIB0::5::INSTR
  PSU2_ADDR=USB0::0x2A8D::0xXXXX::MY123456::INSTR
  SIGGEN_ADDR=TCPIP0::192.168.1.50::INSTR
  SPECAN_ADDR=TCPIP0::192.168.1.60::hislip0::INSTR
  LOG_LEVEL=INFO
  SCPI_TRACE=false

Pairing/roles file (CSV example):
  psu,output,role,label
  ps1,1,gate,Gate A
  ps2,2,drain,Drain A

Running
-------
  python main.py

Typical flow:
  1. Device Manager → enumerate & connect
  2. Pairing → load role file and ensure one-to-one Gate↔Drain
  3. Power Supplies → set V/I, select roles, save presets
  4. Spectrum Analyzer → pick trigger, Arm & Wait (if needed)
  5. Signal Generator → set frequency (Hz/kHz/GHz), RF level, repeat/once
  6. Test Sequencer → set delays (s/ms) and run the recipe

Project Layout
--------------
WorkbenchTest/
├─ app_controller.py
├─ device_man_tab.py
├─ main.py
├─ pairing_tab.py
├─ power_supply.py
├─ power_supply_tab.py
├─ psu_driver.py
├─ signal_gen_tab.py
├─ spectrum_analyzer_tab.py
└─ test_seq_tab.py

Safety
------
- Enforced sequencing: Gate closes before Drain opens; Drain OFF before Gate OFF.
- Ramping: Multi-step with dwell; Emergency Stop should de-energize outputs.
- Interlocks: When enabled, PSU ramp waits for Spectrum Analyzer Arm/Ready.
- Use at your own risk—verify limits per DUT before enabling outputs.

Development
-----------
- Format/lint: black, ruff
- Types: mypy (optional)
- Tests: pytest

  pip install black ruff pytest mypy -q
  ruff check .
  black --check .
  pytest -q

Roadmap
-------
- Bench presets save/load
- Abort conditions (OV/OC thresholds)
- Live plots for current/level during sequences
- Headless CLI mode for automation
