import tkinter as tk
from app_controller import App
import pyvisa

if __name__ == "__main__":
# Root window initialization
    root = tk.Tk()
    app = App(root)
    root.mainloop()
 