from tkinter.ttk import Frame, Style
from tkinter import BOTH, Tk
from scribus import *

class Okno(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent=parent
        self.inicjalizuj()
    def inicjalizuj(self):
        self.parent.title("Book script")
        self.styl=Style()
        self.styl.theme_use("default")
        self.pack(fill=BOTH, expand=1)
def main():
    gui=Tk()
    gui.geometry("1000x700")
    app=Okno(gui)
    gui.mainloop()
if __name__ == '__main__':
    main()
pass