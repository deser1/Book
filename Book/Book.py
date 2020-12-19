from tkinter.ttk import Frame, Style
from tkinter import BOTH, Tk
import sys
try:
    import scribus
except ImportError:
    print("Unable to import the 'scribus' module. This script will only run within")
    print("the Python interpreter embedded in Scribus. Try Script->Execute Script.")
    sys.exit(1)


class Okno(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.styl = Style()
        self.parent = parent
        self.inicjalizuj()

    def inicjalizuj(self):
        self.parent.title("Book script")
        self.styl.theme_use("default")
        self.pack(fill=BOTH, expand=1)


def main():
    gui = Tk()
    gui.geometry("1000x700")
    app = Okno(gui)
    gui.mainloop()


if __name__ == '__main__':
    main()
pass
