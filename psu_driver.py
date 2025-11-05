class BasePSUDriver:
    def __init__(self, instrument):
        self.instrument = instrument

    def select_channel(self, ch):
        pass

    def set_voltage(self, ch, voltage):
        pass

    def set_current(self, ch, current):
        pass

    def enable_output(self, ch):
        pass

    def disable_output(self, ch):
        pass

    def apply_output(self, ch, voltage, current):
        self.set_voltage(ch, voltage)
        self.set_current(ch, current)
        self.enable_output(ch)


class AgilentE3648ADriver(BasePSUDriver):
    def select_channel(self, ch):
        self.instrument.write(f"INST:SEL OUT{ch}")

    def set_voltage(self, ch, voltage):
        self.select_channel(ch)
        self.instrument.write(f"VOLT {voltage}")

    def set_current(self, ch, current):
        self.select_channel(ch)
        self.instrument.write(f"CURR {current}")

    def enable_output(self, ch):
        self.select_channel(ch)
        self.instrument.write("OUTP ON")

    def disable_output(self, ch):
        self.select_channel(ch)
        self.instrument.write("OUTP OFF")


class KeysightU2044XADriver(BasePSUDriver):
    def select_channel(self, ch):
        pass

    def set_voltage(self, ch, voltage):
        self.instrument.write(f"SOUR:VOLT {voltage}")

    def set_current(self, ch, current):
        self.instrument.write(f"SOUR:CURR {current}")

    def enable_output(self, ch):
        self.instrument.write("OUTP ON")

    def disable_output(self, ch):
        self.instrument.write("OUTP OFF")


class KeysightE36312ADriver(BasePSUDriver):
    def select_channel(self, ch):
        self.instrument.write(f"INST:SEL CH{ch}")

    def set_voltage(self, ch, voltage):
        self.select_channel(ch)
        self.instrument.write(f"VOLT {voltage}")

    def set_current(self, ch, current):
        self.select_channel(ch)
        self.instrument.write(f"CURR {current}")

    def enable_output(self, ch):
        self.select_channel(ch)
        self.instrument.write("OUTP ON")

    def disable_output(self, ch):
        self.select_channel(ch)
        self.instrument.write("OUTP OFF")


class KeysightE36232ADriver(BasePSUDriver):
    def set_voltage(self, ch, voltage):
        self.instrument.write(f"APPL {voltage}, 0")  # default current to 0

    def set_current(self, ch, current):
        pass  # No separate current set supported by this command?

    def enable_output(self, ch):
        self.instrument.write("OUTP 1")

    def disable_output(self, ch):
        self.instrument.write("OUTP 0")


class KeysightE36234ADriver(BasePSUDriver):
    def select_channel(self, ch):
        self.instrument.write(f"INST:SEL CH{ch}")

    def set_voltage(self, ch, voltage):
        self.select_channel(ch)
        self.instrument.write(f"VOLT {voltage}")

    def set_current(self, ch, current):
        self.select_channel(ch)
        self.instrument.write(f"CURR {current}")

    def enable_output(self, ch):
        self.select_channel(ch)
        self.instrument.write("OUTP ON")

    def disable_output(self, ch):
        self.select_channel(ch)
        self.instrument.write("OUTP OFF")
