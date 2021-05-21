import string
from tkinter.ttk import *
from tkinter import *
import sys

try:
    import scribus
except ImportError:
    print("Unable to import the 'scribus' module. This script will only run within")
    print("the Python interpreter embedded in Scribus. Try Script->Execute Script.")
    sys.exit(1)
if not scribus.haveDoc():
    scribus.messageBox('Scribus - Script Error', "No document open", scribus.ICON_WARNING, scribus.BUTTON_OK)
    sys.exit(1)


def page_count():
    pagenum: int = scribus.pageCount()
    return pagenum


def reverse(text):
    result = ""
    for i in range(len(text), 0, -1):
        result += text[i - 1]
    return result


def book_page(pages=None):
    pagenum: int = page_count()
    strpages: string = ''
    if pages is None:
        pages = []
    # pagenumrvs = list(reversed(pagenum))
    for i in range(0, pagenum):
        pages[i] = i
        strpages += pages[i] + int(',')
    return strpages


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
    # Label Page Count
    var = StringVar()
    var.set("Page count: " + str(page_count()))
    label = Label(gui, textvariable=var, relief=FLAT)  # RAISED OR FLAT(DEFAULT)
    label.pack()
    # End Label Page Count
    # Label Page Count
    var2 = StringVar()
    str_book = book_page()
    var2.set("Page book: " + str(book_page()))
    label2 = Label(gui, textvariable=var2, relief=FLAT)  # RAISED OR FLAT(DEFAULT)
    label2.pack()
    # End Label Page Count
    app = Okno(gui)
    gui.mainloop()


if __name__ == '__main__':
    main()
pass
