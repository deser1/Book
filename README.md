# Scribus Imposition Script (Book.py)

Zaawansowany skrypt Python dla programu Scribus, służący do automatycznej impozycji (składkowania) dokumentów do druku. Skrypt został zaprojektowany z myślą o profesjonalnych przygotowalniach DTP, oferując funkcje niezbędne w nowoczesnej poligrafii.

## Nowości w wersji 2.0 (Professional Edition)

- **Kompensacja Wypychania (Creep / Shingling)**: Automatyczne przesuwanie stron wewnętrznych w stronę grzbietu, aby zniwelować efekt grubości papieru w zeszytach.
- **Znaczniki Kompletowania (Collation Marks)**: Generowanie "schodków" na grzbiecie składek (w trybie Klejonym), umożliwiających optyczną kontrolę kolejności składek w introligatorni.
- **Znaczniki Falcowania (Fold Marks)**: Linie przerywane wskazujące oś złamu arkusza.
- **Opis Techniczny (Slug)**: Automatyczny opis każdego arkusza (nazwa pliku, data, numer arkusza, strona, numer składki).

## Funkcje

Skrypt obsługuje profesjonalne metody impozycji drukarskiej:

1.  **Broszura (Saddle Stitch)**:
    - Układanie stron w składki wkładane jedna w drugą (do szycia drutem).
    - Automatyczne parowanie stron (np. ostatnia z pierwszą).
    - Obsługa Wypychania (Creep).
2.  **Klejona (Perfect Bound)**:
    - Podział na składki (np. 16 lub 32-stronicowe), które układa się w stos i klei w grzbiecie.
    - Automatyczne generowanie Znaczników Kompletowania (Schodków) na grzbiecie.
3.  **Cięcie i Stos (Cut & Stack)**:
    - Układ 2-użytkowy, gdzie po przecięciu stosu na pół i przełożeniu prawej części pod lewą otrzymujemy prawidłową kolejność (idealne do druku cyfrowego).
4.  **Wieloużytek (N-up)**:
    - Siatka użytków (np. wizytówki) na arkuszu (2x2, 2x3 itd.).

### Dodatkowe możliwości:

- **Obsługa PDF i SLA**: Jako źródło można wskazać zewnętrzny plik PDF lub aktualnie otwarty dokument Scribusa.
- **Formaty produkcyjne**: Obsługa standardowych formatów arkusza (A3, A2, A1, B1, B2, SRA3, RA1).
- **Metody druku**:
  - Standard (Sheetwise) - Przód i Tył na osobnych formach.
  - Work-and-Turn (Obracanie przez bok).
  - Work-and-Tumble (Przewracanie przez głowę).
  - Simplex (Jednostronnie).
- **Znaczniki drukarskie**:
  - Automatyczne generowanie **paserów** (Registration Marks).
  - Pasek kontrolny **CMYK** (Color Bars).
  - **Znaczniki cięcia** (Crop Marks) wokół każdego użytku.
  - **Znaczniki falcowania** (Fold Marks).
  - Wszystkie znaczniki umieszczane są na warstwach wektorowych.
- **Kalkulator Grzbietu**: Wbudowana baza papierów (Offset, Kreda, Munken) do obliczania grubości grzbietu.
- **Podgląd**: Interaktywny podgląd układu arkuszy przed wygenerowaniem.

## Wymagania

- **Scribus**: Wersja 1.5.6+ lub 1.6.x (zalecane).
- **Python**: Wbudowany w Scribus (z biblioteką `tkinter` - standard na Windows/Linux).
- **Ghostscript**: Zalecany do poprawnego importu PDF w Scribusie (niezbędny do podglądu PDF w ramkach).

## Instalacja

1.  Pobierz plik `Book.py`.
2.  Umieść go w dowolnym folderze na dysku (np. w folderze ze skryptami Scribusa).

## Jak używać

1.  Otwórz program **Scribus**.
2.  (Opcjonalnie) Otwórz dokument `.sla`, który chcesz złożyć.
3.  W menu wybierz: **Skrypt** -> **Wykonaj skrypt...**
4.  Wybierz plik `Book.py`.
5.  W oknie skryptu:
    - **Źródło**: Wybierz "Aktualny dokument" lub wskaż plik PDF.
    - **Metoda**: Wybierz rodzaj impozycji (np. Broszura).
    - **Arkusz**: Wybierz format docelowy (np. SRA3) i orientację.
    - **Parametry**: 
        - **Spad (Bleed)**: standardowo 3mm.
        - **Odstęp (Gap)**: odstęp między stronami (dla oprawy klejonej ustaw 0mm, jeśli masz marginesy w dokumencie).
        - **Papier (mm)**: Grubość pojedynczej kartki (np. 0.1) - **Kluczowe dla funkcji Creep!**
6.  Kliknij **PRZELICZ PODGLĄD**, aby zobaczyć układ.
7.  Kliknij **GENERUJ DOKUMENT**.
    - Skrypt zapyta o ścieżkę zapisu (jeśli zaznaczono "Zapisz automatycznie").
    - Po chwili (zależnie od ilości stron) otworzy się nowe okno Scribusa z gotową impozycją.

## Rozwiązywanie problemów

- **Scribus "zamraża się" podczas generowania**:
  - Skrypt intensywnie korzysta z API. Przy dużej liczbie stron (np. >100) operacja może potrwać kilka minut. Pasek postępu na dole okna Scribusa pokazuje stan.
- **Brak podglądu obrazków w oknie skryptu**:
  - To normalne. Python w Scribusie nie posiada biblioteki PIL/Pillow, więc podgląd jest symboliczny (numery stron i układ).
- **Błąd "SystemError" lub "AttributeError"**:
  - Upewnij się, że masz kompatybilną wersję Scribusa (1.5.6+).

## Autor

Skrypt stworzony przez Domek Software
Licencja: MIT / Public Domain (do dowolnego użytku).

---

# English Version

# Scribus Imposition Script (Book.py)

An advanced Python script for Scribus that automates document imposition for professional printing. Designed for DTP professionals, it includes essential features for modern offset and digital printing.

## New in Version 2.0 (Professional Edition)

- **Creep Compensation (Shingling)**: Automatically shifts inner pages towards the spine to compensate for paper thickness in saddle-stitched booklets.
- **Collation Marks (Step Marks)**: Generates "step" marks on the spine of signatures (in Perfect Bound mode) for easy visual verification of signature order.
- **Fold Marks**: Dashed lines indicating the folding axis.
- **Slug Info**: Automatic technical description on every sheet (filename, date, sheet number, side, signature number).

## Features

The script supports professional print imposition methods:

1.  **Saddle Stitch**:
    - Pages arranged in nested signatures (for stapling/stitching).
    - Automatic page pairing (e.g., last page with first page).
    - Supports Creep compensation.
2.  **Perfect Bound**:
    - Splits the document into signatures (e.g., 16 or 32 pages) to be stacked and glued at the spine.
    - Automatic generation of Collation Marks on the spine.
3.  **Cut & Stack**:
    - 2-up layout where, after cutting the stack in half and placing the right stack under the left one, the correct page order is maintained (ideal for digital printing).
4.  **N-up (Grid)**:
    - Grid of pages (e.g., business cards) on a sheet (2x2, 2x3, etc.).

### Additional Capabilities:

- **PDF and SLA Support**: You can use an external PDF file or the currently open Scribus document as the source.
- **Production Formats**: Supports standard sheet formats (A3, A2, A1, B1, B2, SRA3, RA1).
- **Print Methods**:
  - Standard (Sheetwise) - Front and Back on separate forms.
  - Work-and-Turn (Rotate by side).
  - Work-and-Tumble (Rotate by head).
  - Simplex (Single-sided).
- **Printer's Marks**:
  - Automatic generation of **Registration Marks**.
  - **CMYK Color Bars**.
  - **Crop Marks** around each page.
  - **Fold Marks**.
  - All marks are placed on separate vector layers.
- **Spine Calculator**: Built-in database of paper types (Offset, Coated, Munken) to calculate spine thickness.
- **Preview**: Interactive preview of sheet layouts before generation.

## Requirements

- **Scribus**: Version 1.5.6+ or 1.6.x (recommended).
- **Python**: Embedded in Scribus (with `tkinter` library - standard on Windows/Linux).
- **Ghostscript**: Recommended for correct PDF import in Scribus (essential for PDF preview in frames).

## Installation

1.  Download the `Book.py` file.
2.  Place it in any folder on your disk (e.g., in the Scribus scripts folder).

## How to Use

1.  Open **Scribus**.
2.  (Optional) Open the `.sla` document you want to impose.
3.  In the menu, select: **Script** -> **Execute Script...**
4.  Select the `Book.py` file.
5.  In the script window:
    - **Source**: Select "Current Document" or choose a PDF file.
    - **Method**: Select the imposition type (e.g., Saddle Stitch).
    - **Sheet**: Select the target format (e.g., SRA3) and orientation.
    - **Parameters**: 
        - **Bleed**: standard 3mm.
        - **Gap**: distance between pages (set to 0mm for perfect binding if margins are in the document).
        - **Paper (mm)**: Single sheet thickness (e.g., 0.1) - **Crucial for Creep function!**
6.  Click **REFRESH PREVIEW** (PRZELICZ PODGLĄD) to see the layout.
7.  Click **GENERATE DOCUMENT** (GENERUJ DOKUMENT).
    - The script will ask for a save path (if "Auto Save" is checked).
    - After a moment (depending on the number of pages), a new Scribus window will open with the ready imposition.

## Troubleshooting

- **Scribus "freezes" during generation**:
  - The script uses the API intensively. For a large number of pages (e.g., >100), the operation may take a few minutes. The progress bar at the bottom of the Scribus window shows the status.
- **No image preview in the script window**:
  - This is normal. Python in Scribus does not have the PIL/Pillow library, so the preview is symbolic (page numbers and layout only).
- **"SystemError" or "AttributeError"**:
  - Ensure you have a compatible version of Scribus (1.5.6+).

## Author

Script created by Domek Software.
License: MIT / Public Domain (free for any use).
