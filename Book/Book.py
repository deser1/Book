#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import math
import tempfile

# --- KONFIGURACJA ŚRODOWISKA ---
try:
    import scribus
except ImportError:
    print("Ten skrypt musi być uruchomiony wewnątrz Scribusa.")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.filedialog as filedialog
    import tkinter.simpledialog as simpledialog
    import tkinter.messagebox as messagebox
except ImportError:
    scribus.messageBox("Błąd", "Brak modułu 'tkinter'. Skrypt wymaga biblioteki GUI.", scribus.ICON_WARNING)
    sys.exit(1)

# --- LOGIKA IMPOZYCJI ---

class ImpositionEngine:
    """
    Silnik obliczający układ stron na arkuszach dla różnych metod impozycji.
    """
    
    # Typy produktu
    TYPE_SADDLE = "Broszura (Saddle Stitch)"
    TYPE_PERFECT = "Klejona (Perfect Bound)"
    TYPE_CUT_STACK = "Cięcie i Stos (Cut & Stack)"
    TYPE_N_UP = "Wieloużytek (N-up / Grid)"
    
    # Metody druku
    METHOD_SHEETWISE = "Standard (Sheetwise) - Przód/Tył"
    METHOD_WORK_TURN = "Obracanie (Work-and-Turn) - Przez bok"
    METHOD_WORK_TUMBLE = "Przewracanie (Work-and-Tumble) - Przez głowę"
    METHOD_SINGLE = "Jednostronnie (Simplex)"

    def __init__(self):
        pass

    def calculate(self, imp_type, print_method, total_pages, params):
        """
        Główna funkcja obliczeniowa.
        Zwraca listę struktur arkuszy:
        [
            { "front": [PageItem, ...], "back": [PageItem, ...] },
            ...
        ]
        Gdzie PageItem to krotka: (numer_strony, x_ratio, y_ratio, w_ratio, h_ratio, rotacja)
        """
        # Normalizacja liczby stron
        pages = self._get_page_list(total_pages)
        
        # Rozdzielenie logiki w zależności od typu
        if imp_type == self.TYPE_SADDLE:
            return self._calc_saddle(pages, print_method)
        elif imp_type == self.TYPE_PERFECT:
            sig_size = params.get('sig_size', 16)
            return self._calc_perfect(pages, print_method, sig_size)
        elif imp_type == self.TYPE_CUT_STACK:
            return self._calc_cut_stack(pages, print_method)
        elif imp_type == self.TYPE_N_UP:
            cols = params.get('cols', 2)
            rows = params.get('rows', 1)
            return self._calc_n_up(pages, print_method, cols, rows)
        
        return []

    def _get_page_list(self, count):
        return list(range(1, count + 1))

    def _pad_pages(self, pages, multiple):
        """Dopełnia listę stron pustymi stronami (None) do wielokrotności"""
        p = list(pages)
        while len(p) % multiple != 0:
            p.append(None)
        return p

    def _create_item(self, page, x, y, w, h, rot=0):
        return (page, x, y, w, h, rot)

    # --- IMPLEMENTACJE METOD ---

    def _calc_saddle(self, pages, method, sig_idx=0, total_sigs=1):
        """Impozycja Zeszytowa (Broszura)"""
        # Wymaga wielokrotności 4 stron
        pages = self._pad_pages(pages, 4)
        sheets = []
        
        total = len(pages)
        num_sheets = total // 4
        
        l, r = 0, total - 1
        
        for i in range(num_sheets):
            p_first = pages[l]      # 1
            p_last = pages[r]       # N
            p_second = pages[l+1]   # 2
            p_second_last = pages[r-1] # N-1
            
            # STANDARD SHEETWISE (Druk Dwustronny)
            # Przy impozycji "Głowa do głowy" (Head-to-Head), strony są układane tak,
            # aby po złożeniu arkusza na pół wzdłuż dłuższej krawędzi (poziomo),
            # a potem wzdłuż krótszej, orientacja była dobra.
            # W prostym schemacie 4-stronicowym (2 strony na arkusz, 1 łam), 
            # zazwyczaj nie obracamy stron (0 stopni), chyba że arkusz wchodzi do maszyny w specyficzny sposób.
            # Tutaj zakładamy standard: strony stoją pionowo.
            
            # Arkusz Zewnętrzny (Front): [Ostatnia | Pierwsza]
            front_items = [
                self._create_item(p_last, 0.0, 0.0, 0.5, 1.0, 0), # Lewa
                self._create_item(p_first, 0.5, 0.0, 0.5, 1.0, 0) # Prawa
            ]
            
            # Arkusz Wewnętrzny (Back): [Druga | Przedostatnia]
            back_items = [
                self._create_item(p_second, 0.0, 0.0, 0.5, 1.0, 0),      # Lewa
                self._create_item(p_second_last, 0.5, 0.0, 0.5, 1.0, 0)  # Prawa
            ]
            
            # Metadata dla Creep i Collation
            # sheet_idx: 0 = zewnętrzny, num_sheets-1 = wewnętrzny (środek)
            meta = {
                "sheet_idx": i,
                "total_sheets": num_sheets,
                "sig_idx": sig_idx,
                "total_sigs": total_sigs
            }

            if method == self.METHOD_SINGLE:
                sheets.append({"front": front_items, "back": [], **meta})
                sheets.append({"front": back_items, "back": [], **meta})
            else:
                sheets.append({"front": front_items, "back": back_items, **meta})
            
            l += 2
            r -= 2
            
        return sheets

    def _calc_perfect(self, pages, method, sig_size):
        """Impozycja Klejona (Składkowa)"""
        # Dzielimy na składki (signatures)
        if sig_size % 4 != 0: sig_size = 16
        pages = self._pad_pages(pages, 4)
        
        # Dopełnij do pełnych składek
        while len(pages) % sig_size != 0:
            pages.append(None)
            
        chunks = [pages[i:i + sig_size] for i in range(0, len(pages), sig_size)]
        all_sheets = []
        total_sigs = len(chunks)
        
        for i, chunk in enumerate(chunks):
            # Każda składka jest jak mała broszura
            sub_sheets = self._calc_saddle(chunk, method, sig_idx=i, total_sigs=total_sigs)
            all_sheets.extend(sub_sheets)
            
        return all_sheets

    def _calc_cut_stack(self, pages, method):
        """Impozycja Cut & Stack (2-up)"""
        # Dzielimy stos na dwie połowy: Góra (1..N/2) i Dół (N/2+1..N)
        pages = self._pad_pages(pages, 2)
        half = len(pages) // 2
        
        stack_1 = pages[:half]
        stack_2 = pages[half:]
        
        sheets = []
        
        # Dla druku dwustronnego (dupleks) bierzemy pary (Przód, Tył) z każdego stosu
        # Stos 1: [1, 2], [3, 4]...
        # Stos 2: [51, 52], [53, 54]...
        
        # Jeśli druk jednostronny:
        # Arkusz 1: [1, 51]
        # Arkusz 2: [2, 52]
        
        step = 2 if method != self.METHOD_SINGLE else 1
        
        for i in range(0, len(stack_1), step):
            p1 = stack_1[i]
            p2 = stack_2[i]
            
            # Przód Arkusza
            front = [
                self._create_item(p1, 0.0, 0.0, 0.5, 1.0), # Lewa (Stos 1)
                self._create_item(p2, 0.5, 0.0, 0.5, 1.0)  # Prawa (Stos 2)
            ]
            
            back = []
            if method != self.METHOD_SINGLE and (i+1 < len(stack_1)):
                p1_back = stack_1[i+1]
                p2_back = stack_2[i+1]
                
                # Tył Arkusza (Dupleks)
                # Rewers strony 1 to strona 2.
                # W druku przez przewracanie (Sheetwise), strona 2 musi być pod stroną 1.
                # Jeśli Przód to [1 | 51], to Tył (patrząc na arkusz) to [52 | 2] 
                # (żeby po obróceniu 2 trafiło pod 1, a 52 pod 51)
                
                back = [
                    self._create_item(p2_back, 0.0, 0.0, 0.5, 1.0), # Lewa (Tył Stosu 2)
                    self._create_item(p1_back, 0.5, 0.0, 0.5, 1.0)  # Prawa (Tył Stosu 1)
                ]
            
            sheets.append({"front": front, "back": back})
            
        return sheets

    def _calc_n_up(self, pages, method, cols, rows):
        """Impozycja N-up (Siatka)"""
        per_sheet = cols * rows
        sheets = []
        
        # Czy strony mają być unikalne (książka) czy powielone (wizytówki)?
        # Zakładamy tryb książki (unikalne strony po kolei)
        pages = self._pad_pages(pages, per_sheet if method == self.METHOD_SINGLE else per_sheet * 2)
        
        idx = 0
        while idx < len(pages):
            front_items = []
            back_items = []
            
            # Wypełnianie przodu
            for r in range(rows):
                for c in range(cols):
                    if idx < len(pages):
                        w = 1.0 / cols
                        h = 1.0 / rows
                        x = c * w
                        y = r * h
                        front_items.append(self._create_item(pages[idx], x, y, w, h))
                        idx += 1
            
            # Wypełnianie tyłu (jeśli nie simplex)
            if method != self.METHOD_SINGLE:
                # Dla tyłu musimy odwrócić kolejność kolumn (lustrzane odbicie), 
                # aby strona 2 trafiła na plecy strony 1
                # Ale tutaj po prostu bierzemy kolejne strony z listy.
                
                # Buforujemy stronę tyłu
                back_page_grid = [[None for _ in range(cols)] for _ in range(rows)]
                
                for r in range(rows):
                    for c in range(cols):
                        if idx < len(pages):
                            back_page_grid[r][c] = pages[idx]
                            idx += 1
                            
                # Generujemy items z uwzględnieniem lustrzanego odbicia kolumn
                # Kolumna 0 na Tyle to plecy Kolumny (Max) na Przodzie.
                # Jeśli Przód [1][2], to Tył [4][3] -> 3 pod 1, 4 pod 2? Nie.
                # Przód: [1 2]
                # Tył:   [2 1] (żeby 2 było za 1)? Nie, to kolejne strony.
                # Przód: [1 3]
                #        [5 7]
                # Tył:   [4 2]
                #        [8 6]
                
                for r in range(rows):
                    for c in range(cols):
                        # Lustrzana kolumna
                        mirror_c = (cols - 1) - c
                        pg = back_page_grid[r][mirror_c]
                        
                        w = 1.0 / cols
                        h = 1.0 / rows
                        x = c * w
                        y = r * h
                        
                        if pg is not None:
                            back_items.append(self._create_item(pg, x, y, w, h))

            sheets.append({"front": front_items, "back": back_items})
            
        return sheets


# --- GUI ---

class ImpositionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scribus Impozycja Master")
        self.root.geometry("1000x750")
        
        self.engine = ImpositionEngine()
        self.preview_data = []
        self.current_sheet_idx = 0
        
        # Stan
        self.src_file = ""
        self.page_count = 0
        
        # Zmienne GUI
        self.v_src_mode = tk.StringVar(value="current")
        self.v_imp_type = tk.StringVar(value=ImpositionEngine.TYPE_SADDLE)
        self.v_print_method = tk.StringVar(value=ImpositionEngine.TYPE_SADDLE) # Bug fix: use separate var?
        self.v_print_method.set(ImpositionEngine.METHOD_SHEETWISE)
        
        self.v_sheet_fmt = tk.StringVar(value="A3")
        self.v_orient = tk.StringVar(value="Landscape")
        
        # Parametry
        self.v_gap = tk.DoubleVar(value=0.0)
        self.v_bleed = tk.DoubleVar(value=3.0)
        self.v_paper_thickness = tk.DoubleVar(value=0.1) # Grubość papieru w mm
        self.v_sig_size = tk.IntVar(value=16)
        self.v_nup_cols = tk.IntVar(value=2)
        self.v_nup_rows = tk.IntVar(value=2)
        self.v_page_count = tk.IntVar(value=0) # Zmienna GUI dla liczby stron
        self.v_page_count.trace("w", self._on_page_count_change)
        
        self.v_auto_save = tk.BooleanVar(value=True)
        self.v_output_path = tk.StringVar(value=os.path.expanduser("~"))

        # Wyniki z GUI do przekazania do main()
        self.ready_to_generate = False
        self.gen_params = {}

        self._setup_ui()
        self._check_context()

    def _on_page_count_change(self, *args):
        # Wywoływane przez trace na v_page_count
        self._recalc_preview()

    def _open_spine_calculator(self):
        # Okno dialogowe
        dlg = tk.Toplevel(self.root)
        dlg.title("Kalkulator Grzbietu")
        
        # Pozycjonowanie okna
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 50
        dlg.geometry(f"320x300+{x}+{y}")
        
        # Dane papierów (grubość 1 kartki w mm)
        # 1 kartka = 2 strony
        papers = {
            "Offset 80g (Standard)": 0.100,
            "Offset 90g": 0.110,
            "Kreda 115g (Mat/Błysk)": 0.090,
            "Kreda 130g": 0.105,
            "Kreda 150g": 0.120,
            "Kremowy 70g (Vol 2.0)": 0.140,
            "Kremowy 80g (Vol 1.5)": 0.120,
            "Munken Print Cream 90g (Vol 1.5)": 0.135,
            "Munken Print White 90g (Vol 1.5)": 0.135,
            "Objętościowy 60g (Vol 2.0)": 0.120
        }
        
        f = ttk.Frame(dlg, padding=10)
        f.pack(fill="both", expand=True)
        
        ttk.Label(f, text="Liczba Stron (Wnętrze):").pack(pady=5)
        v_pages = tk.IntVar(value=self.page_count if self.page_count > 0 else 100)
        ttk.Entry(f, textvariable=v_pages).pack()
        
        ttk.Label(f, text="Rodzaj Papieru:").pack(pady=5)
        v_paper = tk.StringVar(value="Offset 80g (Standard)")
        cb = ttk.Combobox(f, textvariable=v_paper, values=list(papers.keys()), state="readonly", width=30)
        cb.pack()
        
        v_result = tk.StringVar(value="---")
        
        def calc(*args):
            try:
                pgs = v_pages.get()
                thick = papers[v_paper.get()]
                # Grzbiet = (strony / 2) * grubość_arkusza
                # Dodajmy margines bezpieczeństwa 0.5mm na klej?
                res = (pgs / 2) * thick
                v_result.set(f"{res:.2f}")
            except:
                v_result.set("Błąd")
        
        cb.bind("<<ComboboxSelected>>", calc)
        
        ttk.Button(f, text="Oblicz", command=calc).pack(pady=10)
        
        res_frame = ttk.Frame(f)
        res_frame.pack(pady=5)
        ttk.Label(res_frame, text="Wynik: ").pack(side="left")
        ttk.Label(res_frame, textvariable=v_result, font=("Arial", 12, "bold"), foreground="blue").pack(side="left")
        ttk.Label(res_frame, text=" mm").pack(side="left")
        
        def apply():
            try:
                val = float(v_result.get())
                self.v_spine.set(val)
                dlg.destroy()
            except: pass
            
        ttk.Button(f, text="Zastosuj", command=apply).pack(pady=10)
        
        # Wywołaj raz na starcie
        calc()

    def _setup_ui(self):
        # Główny kontener
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        frame_left = ttk.Frame(paned, width=350)
        frame_right = ttk.Frame(paned)
        paned.add(frame_left)
        paned.add(frame_right)
        
        # --- LEWY PANEL (OPCJE) ---
        
        # 1. Źródło
        lf_src = ttk.LabelFrame(frame_left, text="1. Źródło")
        lf_src.pack(fill="x", padx=5, pady=5)
        
        ttk.Radiobutton(lf_src, text="Aktualny dokument Scribus", variable=self.v_src_mode, value="current", command=self._check_context).pack(anchor="w", padx=5)
        ttk.Radiobutton(lf_src, text="Zewnętrzny plik PDF", variable=self.v_src_mode, value="pdf", command=self._browse_pdf).pack(anchor="w", padx=5)
        
        self.lbl_file_info = ttk.Label(lf_src, text="Brak dokumentu", foreground="gray")
        self.lbl_file_info.pack(anchor="w", padx=20)
        
        # Pole edycji liczby stron
        f_pgs = ttk.Frame(lf_src)
        f_pgs.pack(fill="x", padx=20, pady=2)
        ttk.Label(f_pgs, text="Liczba stron:").pack(side="left")
        self.ent_pages = ttk.Entry(f_pgs, textvariable=self.v_page_count, width=5)
        self.ent_pages.pack(side="left", padx=5)
        # self.ent_pages.bind("<FocusOut>", lambda e: self._recalc_preview())
        # self.ent_pages.bind("<Return>", lambda e: self._recalc_preview())

        # 2. Impozycja
        lf_imp = ttk.LabelFrame(frame_left, text="2. Ustawienia Impozycji")
        lf_imp.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(lf_imp, text="Rodzaj prac:").pack(anchor="w", padx=5)
        cb_type = ttk.Combobox(lf_imp, textvariable=self.v_imp_type, values=[
            ImpositionEngine.TYPE_SADDLE,
            ImpositionEngine.TYPE_PERFECT,
            ImpositionEngine.TYPE_CUT_STACK,
            ImpositionEngine.TYPE_N_UP
        ], state="readonly")
        cb_type.pack(fill="x", padx=5, pady=2)
        cb_type.bind("<<ComboboxSelected>>", self._update_dynamic_opts)
        
        ttk.Label(lf_imp, text="Metoda druku:").pack(anchor="w", padx=5, pady=(5,0))
        cb_method = ttk.Combobox(lf_imp, textvariable=self.v_print_method, values=[
            ImpositionEngine.METHOD_SHEETWISE,
            ImpositionEngine.METHOD_WORK_TURN,
            ImpositionEngine.METHOD_WORK_TUMBLE,
            ImpositionEngine.METHOD_SINGLE
        ], state="readonly")
        cb_method.pack(fill="x", padx=5, pady=2)
        cb_method.bind("<<ComboboxSelected>>", self._recalc_preview_event)

        # Opcje dynamiczne
        self.f_dynamic = ttk.Frame(lf_imp)
        self.f_dynamic.pack(fill="x", padx=5, pady=5)
        
        # Parametry techniczne
        f_tech = ttk.Frame(lf_imp)
        f_tech.pack(fill="x", padx=5, pady=5)
        ttk.Label(f_tech, text="Spad (mm):").pack(side="left")
        ttk.Entry(f_tech, textvariable=self.v_bleed, width=4).pack(side="left", padx=2)
        ttk.Label(f_tech, text="Odstęp:").pack(side="left", padx=2)
        ttk.Entry(f_tech, textvariable=self.v_gap, width=4).pack(side="left", padx=2)
        
        ttk.Label(f_tech, text="Papier (mm):").pack(side="left", padx=2)
        ttk.Entry(f_tech, textvariable=self.v_paper_thickness, width=4).pack(side="left", padx=2)
        
        # Opcje Okładki
        self.v_cover = tk.BooleanVar(value=False)
        self.v_spine = tk.DoubleVar(value=5.0) # mm
        
        f_cover = ttk.Frame(lf_imp)
        f_cover.pack(fill="x", padx=5, pady=5)
        ttk.Checkbutton(f_cover, text="Generuj Okładkę", variable=self.v_cover, command=self._toggle_spine).pack(side="left")
        
        self.lbl_spine = ttk.Label(f_cover, text="Grzbiet (mm):", state="disabled")
        self.lbl_spine.pack(side="left", padx=5)
        self.ent_spine = ttk.Entry(f_cover, textvariable=self.v_spine, width=5, state="disabled")
        self.ent_spine.pack(side="left")
        
        self.btn_calc = ttk.Button(f_cover, text="Kalkulator", command=self._open_spine_calculator, state="disabled")
        self.btn_calc.pack(side="left", padx=5)

        # 3. Arkusz
        lf_sheet = ttk.LabelFrame(frame_left, text="3. Arkusz Docelowy")
        lf_sheet.pack(fill="x", padx=5, pady=5)
        
        f_fmt = ttk.Frame(lf_sheet)
        f_fmt.pack(fill="x", padx=5)
        ttk.Label(f_fmt, text="Format:").pack(side="left")
        cb_fmt = ttk.Combobox(f_fmt, textvariable=self.v_sheet_fmt, values=["A3", "A2", "A4", "SRA3", "B1", "B2", "RA1"], width=8)
        cb_fmt.pack(side="left", padx=5)
        cb_fmt.bind("<<ComboboxSelected>>", self._recalc_preview_event)
        
        f_orient = ttk.Frame(lf_sheet)
        f_orient.pack(fill="x", padx=5, pady=2)
        ttk.Radiobutton(f_orient, text="Poziomo", variable=self.v_orient, value="Landscape", command=self._recalc_preview).pack(side="left")
        ttk.Radiobutton(f_orient, text="Pionowo", variable=self.v_orient, value="Portrait", command=self._recalc_preview).pack(side="left", padx=10)

        # 4. Generowanie
        lf_out = ttk.LabelFrame(frame_left, text="4. Wynik")
        lf_out.pack(fill="x", padx=5, pady=5)
        
        ttk.Checkbutton(lf_out, text="Zapisz automatycznie", variable=self.v_auto_save).pack(anchor="w", padx=5)
        
        f_path = ttk.Frame(lf_out)
        f_path.pack(fill="x", padx=5, pady=2)
        ttk.Entry(f_path, textvariable=self.v_output_path).pack(side="left", fill="x", expand=True)
        ttk.Button(f_path, text="...", width=3, command=self._browse_output).pack(side="left", padx=2)

        ttk.Button(frame_left, text="PRZELICZ PODGLĄD", command=self._recalc_preview).pack(fill="x", padx=10, pady=10)
        
        btn_gen = tk.Button(frame_left, text="GENERUJ DOKUMENT", bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"), height=2, command=self._generate)
        btn_gen.pack(fill="x", side="bottom", padx=10, pady=10)

        # --- PRAWY PANEL (PODGLĄD) ---
        f_nav = ttk.Frame(frame_right)
        f_nav.pack(fill="x", pady=5)
        ttk.Button(f_nav, text="<< Poprzedni", command=self._prev_sheet).pack(side="left")
        self.lbl_sheet = ttk.Label(f_nav, text="Arkusz 0/0")
        self.lbl_sheet.pack(side="left", padx=20)
        ttk.Button(f_nav, text="Następny >>", command=self._next_sheet).pack(side="left")
        
        self.canvas = tk.Canvas(frame_right, bg="#cccccc")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._update_dynamic_opts()

    def _update_dynamic_opts(self, event=None):
        for w in self.f_dynamic.winfo_children(): w.destroy()
        
        t = self.v_imp_type.get()
        if t == ImpositionEngine.TYPE_PERFECT:
            ttk.Label(self.f_dynamic, text="Rozmiar składki:").pack(side="left")
            cb = ttk.Combobox(self.f_dynamic, textvariable=self.v_sig_size, values=[4, 8, 16, 32], width=5)
            cb.pack(side="left", padx=5)
            cb.bind("<<ComboboxSelected>>", self._recalc_preview_event)
        elif t == ImpositionEngine.TYPE_N_UP:
            ttk.Label(self.f_dynamic, text="Kolumny:").pack(side="left")
            ttk.Entry(self.f_dynamic, textvariable=self.v_nup_cols, width=3).pack(side="left")
            ttk.Label(self.f_dynamic, text="Wiersze:").pack(side="left", padx=5)
            ttk.Entry(self.f_dynamic, textvariable=self.v_nup_rows, width=3).pack(side="left")
            
        self._recalc_preview()

    def _toggle_spine(self):
        st = "normal" if self.v_cover.get() else "disabled"
        self.lbl_spine.config(state=st)
        self.ent_spine.config(state=st)
        self.btn_calc.config(state=st)

    def _recalc_preview_event(self, event):
        self._recalc_preview()

    def _check_context(self):
        if self.v_src_mode.get() == "current":
            if scribus.haveDoc():
                self.src_file = scribus.getDocName()
                self.page_count = scribus.pageCount()
                self.v_page_count.set(self.page_count) # Synchronizacja GUI
                w, h = scribus.getPageSize()
                self.lbl_file_info.config(text=f"SLA: {self.page_count} str. ({int(w)}x{int(h)}mm)")
                base = os.path.splitext(self.src_file)[0]
                self.v_output_path.set(base + "_impozycja.sla")
                self._recalc_preview()
            else:
                self.lbl_file_info.config(text="Brak otwartego pliku SLA")

    def _browse_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.src_file = path
            
            # Próba automatycznego wykrycia liczby stron
            cnt = self._get_pdf_page_count(path)
            
            if not cnt or cnt <= 0:
                cnt = simpledialog.askinteger("PDF", "Podaj liczbę stron w pliku PDF:", initialvalue=4)
            
            if cnt:
                self.page_count = cnt
                self.v_page_count.set(cnt) # Aktualizacja pola w GUI
                self.lbl_file_info.config(text=f"PDF: {os.path.basename(path)} ({cnt} str.)")
                base = os.path.splitext(path)[0]
                self.v_output_path.set(base + "_impozycja.sla")
                self._recalc_preview()

    def _get_pdf_page_count(self, filename):
        try:
            with open(filename, "rb") as f:
                content = f.read()
                import re
                matches = re.findall(rb"/Type\s*/Pages\b[^>]*\/Count\s+(\d+)", content)
                if matches:
                    counts = [int(x) for x in matches]
                    return max(counts)
                matches = re.findall(rb"/Type\s*/Page\b", content)
                if matches:
                    return len(matches)
        except:
            pass
        return 0

    def _recalc_preview(self):
        try:
             # Pobierz z GUI
             val = self.v_page_count.get()
             self.page_count = val
        except:
             # Jeśli błąd (np. puste pole), uznaj że 0
             self.page_count = 0
        
        if not self.page_count or self.page_count <= 0:
             self.preview_data = []
             self.canvas.delete("all")
             self.lbl_sheet.config(text="Brak danych")
             return
        
        params = {
            "sig_size": self.v_sig_size.get(),
            "cols": self.v_nup_cols.get(),
            "rows": self.v_nup_rows.get()
        }
        
        self.preview_data = self.engine.calculate(
            self.v_imp_type.get(),
            self.v_print_method.get(),
            self.page_count,
            params
        )
        
        if self.v_cover.get() and self.v_imp_type.get() != ImpositionEngine.TYPE_N_UP:
            self.current_sheet_idx = -1
        else:
            self.current_sheet_idx = 0
            
        self._draw_sheet()

    def _draw_sheet(self):
        self.canvas.delete("all")
        if not self.preview_data: return
        
        if self.current_sheet_idx == -1:
            self.lbl_sheet.config(text="OKŁADKA")
            self._draw_cover_preview()
            return

        sheet = self.preview_data[self.current_sheet_idx]
        total = len(self.preview_data)
        self.lbl_sheet.config(text=f"Arkusz {self.current_sheet_idx+1} / {total}")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10: w=600; h=400
        
        # Marginesy wizualne
        m = 20
        
        # Rysujemy dwie strony arkusza (Przód i Tył) obok siebie
        # Chyba że jednostronny
        method = self.v_print_method.get()
        
        area_w = (w - 3*m) / 2
        area_h = h - 2*m
        
        # Przód (Lewa strona ekranu)
        self._draw_surface(sheet["front"], m, m, area_w, area_h, "AWERS (Przód)")
        
        # Tył (Prawa strona ekranu) - jeśli istnieje
        if sheet["back"]:
            self._draw_surface(sheet["back"], m*2 + area_w, m, area_w, area_h, "REWERS (Tył)")
        elif method == ImpositionEngine.METHOD_WORK_TURN:
            self._draw_surface(sheet["front"], m*2 + area_w, m, area_w, area_h, "REWERS (Ten sam co Awers)")

    def _draw_surface(self, items, x, y, w, h, title):
        # Tło papieru
        self.canvas.create_rectangle(x, y, x+w, y+h, fill="white", outline="black", width=2)
        self.canvas.create_text(x + w/2, y - 10, text=title, font=("Arial", 9, "bold"))
        
        # Siatka centrująca (krzyże)
        cx, cy = x + w/2, y + h/2
        self.canvas.create_line(x, cy, x+w, cy, fill="#ddd", dash=(2,4))
        self.canvas.create_line(cx, y, cx, y+h, fill="#ddd", dash=(2,4))
        
        for item in items:
            # item = (page, xr, yr, wr, hr, rot)
            pg, xr, yr, wr, hr, rot = item
            
            px = x + xr * w
            py = y + yr * h
            pw = wr * w
            ph = hr * h
            
            # Margines wewnątrz użytku
            g = 2
            
            color = "#E8F5E9" if pg else "#f0f0f0"
            txt = str(pg) if pg else "X"
            
            self.canvas.create_rectangle(px+g, py+g, px+pw-g, py+ph-g, fill=color, outline="#4CAF50")
            self.canvas.create_text(px+pw/2, py+ph/2, text=txt, font=("Arial", 14, "bold"), fill="#2E7D32")

    def _draw_cover_preview(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        spine = self.v_spine.get()
        
        # Mapowanie formatów (kopia z run_imposition_job dla podglądu)
        sizes = {
            "A4": (210.0, 297.0), "A3": (297.0, 420.0), "A2": (420.0, 594.0),
            "SRA3": (320.0, 450.0), "B1": (700.0, 1000.0), "RA1": (610.0, 860.0),
            "B2": (500.0, 707.0), "B3": (353.0, 500.0)
        }
        fw, fh = sizes.get(self.v_sheet_fmt.get(), (297.0, 420.0))
        if self.v_orient.get() == "Landscape": fw, fh = fh, fw
        
        # Przybliżony rozmiar strony netto (1/2 arkusza)
        page_w = fw / 2
        page_h = fh
        
        total_w = (page_w * 2) + spine
        total_h = page_h
        
        margin = 20
        if total_w == 0: total_w = 100
        if total_h == 0: total_h = 100
        
        scale = min((cw - 2*margin)/total_w, (ch - 2*margin)/total_h)
        
        dw = total_w * scale
        dh = total_h * scale
        dx = (cw - dw) / 2
        dy = (ch - dh) / 2
        
        self.canvas.create_rectangle(dx, dy, dx+dw, dy+dh, outline="black", fill="white", width=2)
        
        cx = dx + dw/2
        sw = spine * scale
        
        self.canvas.create_line(cx - sw/2, dy, cx - sw/2, dy+dh, dash=(4, 2), fill="red")
        self.canvas.create_line(cx + sw/2, dy, cx + sw/2, dy+dh, dash=(4, 2), fill="red")
        
        self.canvas.create_text(dx + (dw/2 - sw/2)/2, dy + dh/2, text="TYŁ (IV)", font=("Arial", 10, "bold"))
        self.canvas.create_text(dx + dw - (dw/2 - sw/2)/2, dy + dh/2, text="PRZÓD (I)", font=("Arial", 10, "bold"))
        self.canvas.create_text(cx, dy + dh/2, text=f"{spine}mm", angle=90, fill="red", font=("Arial", 8))

        # Wymiary
        info = f"Wymiar Okładki: {total_w:.1f} x {total_h:.1f} mm"
        self.canvas.create_text(cw/2, dy + dh + 15, text=info, fill="blue", font=("Arial", 9))

    def _prev_sheet(self):
        min_idx = -1 if (self.v_cover.get() and self.v_imp_type.get() != ImpositionEngine.TYPE_N_UP) else 0
        if self.current_sheet_idx > min_idx:
            self.current_sheet_idx -= 1
            self._draw_sheet()

    def _next_sheet(self):
        if self.current_sheet_idx < len(self.preview_data) - 1:
            self.current_sheet_idx += 1
            self._draw_sheet()

    def _browse_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".sla", filetypes=[("Scribus", "*.sla")])
        if f: self.v_output_path.set(f)

    def _generate(self):
        if not self.preview_data:
            messagebox.showwarning("Info", "Brak danych do wygenerowania.")
            return
            
        # Zapisz parametry w słowniku
        
        # Normalizacja ścieżki dla Scribusa (czasem woli / zamiast \)
        if self.src_file:
            self.src_file = self.src_file.replace("\\", "/")

        self.gen_params = {
            "fmt": self.v_sheet_fmt.get(),
            "orient": 1 if self.v_orient.get() == "Landscape" else 0,
            "preview_data": self.preview_data, # Kopia danych
            "auto_save": self.v_auto_save.get(),
            "output_path": self.v_output_path.get().strip(),
            "src_mode": self.v_src_mode.get(),
            "src_file": self.src_file,
            "gap": self.v_gap.get(),
            "bleed": self.v_bleed.get(),
            "paper_thickness": self.v_paper_thickness.get(),
            "cover": self.v_cover.get(),
            "spine": self.v_spine.get(),
            "imp_type": self.v_imp_type.get()
        }
        
        # Upewnij się co do ścieżki
        if self.gen_params["auto_save"] and self.gen_params["output_path"]:
             raw_path = self.gen_params["output_path"]
             if not os.path.isabs(raw_path):
                 base_dir = os.path.expanduser("~")
                 if self.src_file: base_dir = os.path.dirname(self.src_file)
                 self.gen_params["output_path"] = os.path.join(base_dir, raw_path)

        self.ready_to_generate = True
        self.root.quit()
        # Koniec funkcji, sterowanie wróci do main()

    # (usunąłem stary kod _generate, który robił scribus.newDocument)

    def run_imposition_job(self):
        """Wykonywane po zamknięciu GUI"""
        if not self.ready_to_generate: return
        
        p = self.gen_params
        
        # Mapowanie formatów na wymiary (w mm)
        sizes = {
            "A4": (210.0, 297.0),
            "A3": (297.0, 420.0),
            "A2": (420.0, 594.0),
            "SRA3": (320.0, 450.0),
            "B1": (700.0, 1000.0),
            "RA1": (610.0, 860.0),
            "B2": (500.0, 707.0),
            "B3": (353.0, 500.0)
        }
        
        fmt_arg = sizes.get(p["fmt"], (297.0, 420.0)) # Domyślnie A3
        
        try:
            # newDocument wymaga krotki (width, height) jako pierwszego argumentu w niektórych wersjach
            scribus.newDocument(fmt_arg, (0.0, 0.0, 0.0, 0.0), p["orient"], 1, scribus.UNIT_MILLIMETERS, scribus.PAGE_1, 0, 1)
            doc_w, doc_h = scribus.getPageSize()
            
            # --- GENEROWANIE OKŁADKI (Opcjonalne) ---
            start_page_idx = 1
            
            if p.get("cover") and p["src_mode"] != "nup": # N-up nie ma sensu dla okładki
                spine = p.get("spine", 5.0)
                # Obliczamy wymiar strony netto jako połowę arkusza impozycyjnego
                # To założenie dla broszury/książki (2 strony na arkusz)
                net_w = doc_w / 2
                net_h = doc_h
                
                cover_w = (net_w * 2) + spine
                cover_h = net_h
                
                # Dodaj stronę na początku (jako stronę 1)
                # newPage(-1) dodaje na końcu. Skoro dokument jest pusty (ma 1 stronę defaultową),
                # to zmienimy rozmiar tej pierwszej strony.
                
                scribus.gotoPage(1)
                try:
                    scribus.setPageSize(cover_w, cover_h)
                except: pass
                
                # Rysuj bigi (Registration color)
                try:
                    cx = cover_w / 2
                    sx1 = cx - spine/2
                    sx2 = cx + spine/2
                    
                    # Linie przerywane dla bigu
                    l1 = scribus.createLine(sx1, 0, sx1, cover_h)
                    l2 = scribus.createLine(sx2, 0, sx2, cover_h)
                    
                    # Cache koloru
                    if not hasattr(self, 'reg_color'):
                         self.reg_color = "Registration"
                         if "Registration" not in scribus.getColorNames():
                             self.reg_color = "Black"
                    
                    col = self.reg_color
                    
                    scribus.setLineColor(col, l1)
                    scribus.setLineColor(col, l2)
                    # LINE_DASH może nie być dostępne jako stała w starszym API, użyjmy cyfry
                    try: scribus.setLineStyle(scribus.LINE_DASH, l1)
                    except: pass
                    try: scribus.setLineStyle(scribus.LINE_DASH, l2)
                    except: pass
                    
                    # Opis Grzbietu (Zawsze na zewnątrz, bezpiecznie)
                    # Wstaw opis OBOK na spadzie (nad okładką), wyśrodkowany
                    # Pozycja Y = -10 (10mm nad krawędzią netto)
                    
                    info_text = f"Grzbiet: {spine}mm"
                    
                    # Utwórz ramkę nad okładką
                    t_info = scribus.createText(cx - 30, -15, 60, 10)
                    scribus.setText(info_text, t_info)
                    scribus.setTextAlignment(scribus.ALIGN_CENTER, t_info)
                    scribus.setFontSize(9, t_info)
                    scribus.setLineColor("None", t_info)
                    
                    # Opcjonalnie: Dodaj też napis wewnątrz, jeśli grzbiet szeroki (>10mm)
                    if spine >= 10.0:
                        t_in = scribus.createText(sx1, cover_h/2 - 5, spine, 10)
                        scribus.setText("GRZBIET", t_in)
                        scribus.setTextAlignment(scribus.ALIGN_CENTER, t_in)
                        scribus.setFontSize(8, t_in)
                        scribus.setLineColor("None", t_in)
                        # Obrót o 90 stopni - eksperymentalnie
                        # scribus.setRotation(90, t_in) 
                        # Bezpieczniej zostawić poziomo przy szerokim grzbiecie, albo pominąć.
                        pass

                except: pass
                
                # Skoro strona 1 to okładka, impozycja zaczyna się od strony 2
                start_page_idx = 2
                
                # Strony impozycji zostały już dodane w pętli wyżej (pages_to_add)
            
            # Parametry do place_on_page
            self.current_gap = p["gap"]
            self.current_bleed = p["bleed"]
            self.current_src_mode = p["src_mode"]
            self.current_src_file = p["src_file"]
            self.current_paper_thickness = p.get("paper_thickness", 0.0)
            self.current_imp_type = p.get("imp_type", ImpositionEngine.TYPE_SADDLE)
            
            preview_data = p["preview_data"]
            
            total_doc_pages = 0
            for sheet in preview_data:
                total_doc_pages += 1
                if sheet["back"]: total_doc_pages += 1
            
            # Jeśli okładka jest włączona, pierwsza strona to okładka, a impozycja potrzebuje total_doc_pages nowych stron.
            # Jeśli wyłączona, pierwsza strona to arkusz 1, potrzebujemy (total - 1) nowych.
            
            pages_to_add = total_doc_pages
            if not p.get("cover") or p["src_mode"] == "nup":
                pages_to_add = total_doc_pages - 1
            
            if pages_to_add > 0:
                for _ in range(pages_to_add):
                    scribus.newPage(-1)
            
            # Włącz pasek postępu
            try:
                scribus.progressReset()
                scribus.progressTotal(len(preview_data))
            except: pass
            
            # setRedraw(False) może powodować wrażenie zawieszenia przy dużej ilości obiektów.
            # Włączmy je, żeby widzieć postęp, albo wyłączajmy tylko na chwilę.
            scribus.setRedraw(False) 
            
            page_idx = start_page_idx
            
            # Cache koloru
            self.reg_color = "Registration"
            if "Registration" not in scribus.getColorNames():
                self.reg_color = "Black"

            for i, sheet in enumerate(preview_data):
                try: scribus.progressSet(i+1)
                except: pass
                
                # Ustaw metadane aktualnego arkusza dla funkcji pomocniczych
                self.current_sheet_meta = sheet
                
                scribus.gotoPage(page_idx)
                
                # 1. Treść
                self._place_on_page(sheet["front"], doc_w, doc_h)
                
                # 2. Znaczniki
                self._draw_marks(doc_w, doc_h, "AWERS (Front)", i+1, len(preview_data)) 
                self._draw_all_crop_marks(sheet["front"], doc_w, doc_h)
                
                page_idx += 1
                
                if sheet["back"]:
                    scribus.gotoPage(page_idx)
                    
                    # 1. Treść
                    self._place_on_page(sheet["back"], doc_w, doc_h)
                    
                    # 2. Znaczniki
                    self._draw_marks(doc_w, doc_h, "REWERS (Back)", i+1, len(preview_data))
                    self._draw_all_crop_marks(sheet["back"], doc_w, doc_h)
                    
                    page_idx += 1
                
                # Odśwież co 5 arkuszy, żeby nie wyglądało na zwis
                if i % 5 == 0:
                   scribus.setRedraw(True)
                   scribus.setRedraw(False)
            
            scribus.setRedraw(True)
            try: scribus.progressReset()
            except: pass
            
            msg = "Dokument został wygenerowany w nowym oknie Scribusa.\n"
            if p["auto_save"]:
                path = p["output_path"]
                if path:
                    if not path.lower().endswith(".sla"): path += ".sla"
                    try:
                        scribus.saveDocAs(path)
                        if os.path.exists(path):
                            msg += f"\nSUKCES: Zapisano plik:\n{path}"
                        else:
                            msg += "\nOSTRZEŻENIE: Zapisano, ale brak pliku na dysku."
                    except Exception as e:
                        msg += f"\nBŁĄD ZAPISU:\n{e}"
                else:
                    msg += "\nAnulowano zapis (brak ścieżki)."
            else:
                msg += "\nPlik niezapisany."
                
            scribus.messageBox("Raport", msg, scribus.ICON_INFORMATION)
            
        except Exception as e:
             scribus.setRedraw(True)
             scribus.messageBox("Błąd Krytyczny", str(e), scribus.ICON_WARNING)

    def _draw_marks(self, dw, dh, side_name="", sheet_num=0, total_sheets=0):
        """Rysuje pasery i kostki."""
        
        # Kolor Registration (z cache)
        if hasattr(self, 'reg_color'):
            reg_color = self.reg_color
        else:
            reg_color = "Registration"
            if not reg_color in scribus.getColorNames():
                scribus.defineColor("Registration", 255, 255, 255, 255)
                reg_color = "Registration"
        
        mark_size = 5.0 # mm
        margin = 5.0 # Odstęp od krawędzi arkusza
        
        positions = [
            (margin, margin), # LG
            (dw/2, margin),   # Środek Góra
            (dw-margin, margin), # PG
            (margin, dh-margin), # LD
            (dw/2, dh-margin),   # Środek Dół
            (dw-margin, dh-margin), # PD
            (margin, dh/2), # Środek Lewy
            (dw-margin, dh/2) # Środek Prawy
        ]
        
        for x, y in positions:
            self._draw_reg_mark(x, y, mark_size, reg_color)

        # 2. Pasek kolorów (Color Bar)
        # Rysujemy prostokąty CMYK na dole lub z boku
        # Rozmiar kostki
        box_w = 5.0
        box_h = 5.0
        start_x = dw/2 - (4 * box_w) / 2
        start_y = dh - margin - box_h - 2.0
        
        # Definicje kolorów CMYK (C, M, Y, K)
        cmyk_defs = {
            "Cyan": (255, 0, 0, 0),
            "Magenta": (0, 255, 0, 0),
            "Yellow": (0, 0, 255, 0),
            "Black": (0, 0, 0, 255)
        }
        
        # Upewnij się, że kolory istnieją
        for name, values in cmyk_defs.items():
            if name not in scribus.getColorNames():
                # defineColor(name, c, m, y, k) - wartości 0-255
                scribus.defineColor(name, values[0], values[1], values[2], values[3])

        colors = ["Cyan", "Magenta", "Yellow", "Black"]
        for i, col in enumerate(colors):
            if col in scribus.getColorNames():
                r = scribus.createRect(start_x + i*box_w, start_y, box_w, box_h)
                scribus.setFillColor(col, r)
                scribus.setLineColor("None", r)

        # 3. Znaczniki Falcowania (Fold Marks)
        self._draw_fold_marks(dw, dh, reg_color)

        # 4. Znaczniki Kompletowania (Collation Marks)
        if self.current_imp_type == ImpositionEngine.TYPE_PERFECT:
             self._draw_collation_marks(dw, dh)

        # 5. Opis Arkusza (Slug)
        self._draw_slug_info(dw, dh, side_name, sheet_num, total_sheets)

    def _draw_fold_marks(self, dw, dh, color):
        """Rysuje linie falcowania (przerywane) na marginesach."""
        # Pionowa linia środkowa (Grzbiet)
        # Rysujemy tylko na marginesach (poza obszarem spadu)
        # Zakładamy margines ok 10mm, spad 3mm.
        margin_len = 8.0 
        
        cx = dw / 2
        cy = dh / 2
        
        # Góra
        l1 = scribus.createLine(cx, 0, cx, margin_len)
        scribus.setLineColor(color, l1)
        try: scribus.setLineStyle(scribus.LINE_DASH, l1)
        except: pass
        
        # Dół
        l2 = scribus.createLine(cx, dh - margin_len, cx, dh)
        scribus.setLineColor(color, l2)
        try: scribus.setLineStyle(scribus.LINE_DASH, l2)
        except: pass
        
        # Pozioma (jeśli N-up lub składka krzyżowa - tu zakładamy prosty układ 2-stronny)
        # Opcjonalnie można dodać poziome znaczniki na cy

    def _draw_collation_marks(self, dw, dh):
        """Rysuje schodki (sygnatury) na grzbiecie dla oprawy klejonej."""
        if not hasattr(self, 'current_sheet_meta'): return
        
        meta = self.current_sheet_meta
        sig_idx = meta.get("sig_idx", 0)
        total_sigs = meta.get("total_sigs", 1)
        sheet_idx = meta.get("sheet_idx", 0)
        
        # Rysujemy znacznik tylko na grzbiecie (zewnętrznym zgięciu składki)
        # W standardowej impozycji 4-stronicowej (1 arkusz składany na pół),
        # grzbiet jest na środku (dw/2).
        
        # Schodki powinny być widoczne po złożeniu składki.
        # Rysujemy prostokąt na grzbiecie.
        
        if total_sigs <= 1: return
        
        # Obszar roboczy dla schodków (np. od 20% do 80% wysokości arkusza)
        h_start = dh * 0.2
        h_end = dh * 0.8
        h_avail = h_end - h_start
        
        step_h = h_avail / total_sigs
        
        # Pozycja Y dla danej składki
        y = h_start + (sig_idx * step_h)
        
        # Wymiary znacznika
        mark_w = 4.0 # mm (po 2mm na stronę)
        mark_h = step_h
        
        x = (dw / 2) - (mark_w / 2)
        
        r = scribus.createRect(x, y, mark_w, mark_h)
        scribus.setFillColor("Black", r) # Zwykły czarny (nie Registration), żeby nie brudzić CMY
        scribus.setLineColor("None", r)
        
        # Opcjonalnie: Dodaj tekst z numerem składki obok
        # t = scribus.createText(x + mark_w + 1, y, 10, mark_h)
        # scribus.setText(str(sig_idx+1), t)
        # scribus.setFontSize(6, t)

    def _draw_slug_info(self, dw, dh, side_name, sheet_num, total_sheets):
        """Dodaje opis tekstowy arkusza."""
        info = f"Plik: {os.path.basename(self.current_src_file)} | Data: {self._get_date_str()} | Arkusz: {sheet_num}/{total_sheets} | {side_name}"
        
        # Jeśli mamy metadane składki
        if hasattr(self, 'current_sheet_meta'):
             m = self.current_sheet_meta
             info += f" | Składka: {m.get('sig_idx',0)+1}/{m.get('total_sigs',1)}"
        
        # Umieść na dole po lewej, poza spadem
        x = 10
        y = dh - 8
        w = dw - 20
        h = 6
        
        t = scribus.createText(x, y, w, h)
        scribus.setText(info, t)
        scribus.setFontSize(7, t)
        # scribus.setFont("Arial Regular", t) # Ryzykowne jeśli fontu nie ma
        scribus.setLineColor("None", t)

    def _get_date_str(self):
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    def _draw_reg_mark(self, x, y, size, color):
        # Rysuje paser w punkcie (x,y) - środek pasera
        r = size / 2
        # Kółko
        # o = scribus.createEllipse(x-r, y-r, size, size)
        # scribus.setLineColor(color, o)
        # scribus.setFillColor("None", o)
        # scribus.setLineWidth(0.2, o)
        
        # Krzyż
        l1 = scribus.createLine(x-r, y, x+r, y)
        scribus.setLineColor(color, l1)
        scribus.setLineWidth(0.2, l1)
        
        l2 = scribus.createLine(x, y-r, x, y+r)
        scribus.setLineColor(color, l2)
        scribus.setLineWidth(0.2, l2)

    def _place_on_page(self, items, dw, dh):
        """Umieszcza obiekty na stronie Scribusa"""
        # ... (parametry)
        # Używamy parametrów zapisanych w self (jeśli wywołane z job) lub z GUI
        if hasattr(self, 'current_gap'):
            gap = self.current_gap
            bleed = self.current_bleed
            src_mode = self.current_src_mode
            src_file = self.current_src_file
        else:
            gap = self.v_gap.get()
            bleed = self.v_bleed.get()
            src_mode = self.v_src_mode.get()
            src_file = self.src_file
        
        # W Scribusie jednostki to mm (zgodnie z newDocument)
        
        # Oblicz przesunięcie (Creep / Shingling)
        creep_shift = 0.0
        if hasattr(self, 'current_sheet_meta') and hasattr(self, 'current_paper_thickness'):
             th = self.current_paper_thickness
             if th > 0:
                 meta = self.current_sheet_meta
                 sheet_idx = meta.get("sheet_idx", 0)
                 # Im głębiej (większy sheet_idx), tym bardziej przesuwamy do grzbietu (do środka)
                 creep_shift = sheet_idx * th

        for item in items:
            pg, xr, yr, wr, hr, rot = item
            if pg is None: continue
            
            # Pozycja
            x = xr * dw
            y = yr * dh
            w = wr * dw
            h = hr * dh
            
            # Zastosuj Creep
            if creep_shift > 0:
                # Zakładamy że grzbiet jest pionowo na środku (x=0.5)
                if xr < 0.49: # Lewa strona
                    x += creep_shift
                elif xr > 0.51: # Prawa strona
                    x -= creep_shift
            
            # Ramka (z uwzględnieniem spadu)
            fx = x + gap/2
            fy = y + gap/2
            fw = w - gap
            fh = h - gap
            
            # UWAGA: Obrót strony (rot)
            # Jeśli rot == 180, musimy obrócić zawartość.
            # W Scribusie obracamy ramkę względem środka.
            
            if src_mode == "pdf":
                img = scribus.createImage(fx, fy, fw, fh)
                scribus.loadImage(src_file, img)
                scribus.setScaleImageToFrame(True, True, img)
                try:
                    scribus.setImagePage(pg, img)
                except Exception as e:
                    try: scribus.setImagePage(pg-1, img)
                    except: pass
                
                if rot != 0:
                    scribus.setRotation(rot, img)
                    
            else:
                # Placeholder tekstowy
                txt = scribus.createText(fx, fy, fw, fh)
                scribus.setText(f"Str. {pg}", txt)
                try: scribus.setPrintable(False, txt)
                except: pass
                
                try:
                    scribus.setFontSize(24, txt)
                    scribus.setTextAlignment(scribus.ALIGN_CENTER, txt)
                except: pass
                
                if rot != 0:
                    scribus.setRotation(rot, txt)
            
            # Safe Zone Warning (wizualnie)
            # Rysujemy ramkę bezpieczną 5mm wewnątrz netto, jeśli to nie PDF
            # Albo zawsze, ale na warstwie Guides? Scribus API nie ma guides.
            # Rysujemy prostokąt z cienką linią
            
            # safe_margin = 5.0
            # sx = fx + safe_margin
            # sy = fy + safe_margin
            # sw = fw - 2*safe_margin
            # sh = fh - 2*safe_margin
            # rect = scribus.createRect(sx, sy, sw, sh)
            # scribus.setLineColor("Magenta", rect)
            # scribus.setLineWidth(0.1, rect)
            # try: scribus.setLineStyle(scribus.LINE_DASH, rect)
            # except: pass

    def _draw_all_crop_marks(self, items, dw, dh):
        if hasattr(self, 'current_gap'):
             gap = self.current_gap
        else: gap = 0.0
        
        # Oblicz przesunięcie (Creep) - duplikat logiki z _place_on_page
        creep_shift = 0.0
        if hasattr(self, 'current_sheet_meta') and hasattr(self, 'current_paper_thickness'):
             th = self.current_paper_thickness
             if th > 0:
                 meta = self.current_sheet_meta
                 sheet_idx = meta.get("sheet_idx", 0)
                 creep_shift = sheet_idx * th

        # Znajdź granice bloku (min_x, max_x, min_y, max_y)
        # Aby wiedzieć, które krawędzie są zewnętrzne
        # Zakładamy, że items są znormalizowane (0.0 - 1.0)
        
        # Jeśli gap > 0, rysujemy pełne znaczniki dla każdego użytku.
        # Jeśli gap == 0 (styk), rysujemy tylko zewnętrzne.
        
        draw_inner = (gap > 0.1) # Tolerancja
        
        for item in items:
            pg, xr, yr, wr, hr, rot = item
            if pg is None: continue
            
            x = xr * dw
            y = yr * dh
            
            # Zastosuj Creep (musi być identyczne jak w place_on_page)
            if creep_shift > 0:
                if xr < 0.49: x += creep_shift
                elif xr > 0.51: x -= creep_shift
            
            w = wr * dw
            h = hr * dh
            
            fx = x + gap/2
            fy = y + gap/2
            fw = w - gap
            fh = h - gap
            
            # Określ, które krawędzie są zewnętrzne względem arkusza
            # Margines błędu float
            is_left = (xr < 0.01)
            is_right = (xr + wr > 0.99)
            is_top = (yr < 0.01)
            is_bottom = (yr + hr > 0.99)
            
            # Jeśli gap > 0, traktujemy wszystkie jako zewnętrzne (każdy ma swoje)
            if draw_inner:
                self._draw_crop_marks(fx, fy, fw, fh, True, True, True, True)
            else:
                self._draw_crop_marks(fx, fy, fw, fh, is_left, is_right, is_top, is_bottom)

    def _draw_crop_marks(self, x, y, w, h, left, right, top, bottom):
        """Rysuje linie cięcia wokół użytku (x,y,w,h)."""
        # Długość kreski i odstęp od formatu netto
        l = 5.0
        offset = 2.0
        
        # Kolor Registration (z cache)
        if hasattr(self, 'reg_color'):
            col = self.reg_color
        else:
            col = "Registration"
            if not col in scribus.getColorNames(): col = "Black"
        
        # Lewy Górny
        if top and left:
            # Pionowa
            line = scribus.createLine(x, y - offset - l, x, y - offset)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
            # Pozioma
            line = scribus.createLine(x - offset - l, y, x - offset, y)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
        elif top: # Tylko góra (np. styk dwóch stron)
             # Pionowa na styku? Zazwyczaj rysujemy tylko na rogach bloku.
             # Ale jeśli to środek, to linia cięcia powinna być.
             # Jeśli gap=0, to linia cięcia jest wspólna.
             # Rysujmy tylko na rogach zewnętrznych bloku.
             pass
        
        # Prawy Górny
        if top and right:
            line = scribus.createLine(x + w, y - offset - l, x + w, y - offset)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
            line = scribus.createLine(x + w + offset, y, x + w + offset + l, y)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
        
        # Lewy Dolny
        if bottom and left:
            line = scribus.createLine(x, y + h + offset, x, y + h + offset + l)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
            line = scribus.createLine(x - offset - l, y + h, x - offset, y + h)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
        
        # Prawy Dolny
        if bottom and right:
            line = scribus.createLine(x + w, y + h + offset, x + w, y + h + offset + l)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
            line = scribus.createLine(x + w + offset, y + h, x + w + offset + l, y + h)
            scribus.setLineColor(col, line)
            scribus.setLineWidth(0.1, line)
            
        # Dodatkowe znaczniki środkowe dla styku (jeśli gap=0 i jesteśmy na krawędzi)
        # Np. znaczniki cięcia pionowego na górze i dole między stronami
        if not left and top: # Środek góra
             line = scribus.createLine(x, y - offset - l, x, y - offset)
             scribus.setLineColor(col, line)
             scribus.setLineWidth(0.1, line)
        if not left and bottom: # Środek dół
             line = scribus.createLine(x, y + h + offset, x, y + h + offset + l)
             scribus.setLineColor(col, line)
             scribus.setLineWidth(0.1, line)
        
        # Poziome środkowe (rzadziej potrzebne w książkach, ale w N-up tak)
        if not top and left: # Środek lewo
             line = scribus.createLine(x - offset - l, y, x - offset, y)
             scribus.setLineColor(col, line)
             scribus.setLineWidth(0.1, line)
        if not top and right: # Środek prawo
             line = scribus.createLine(x + w + offset, y, x + w + offset + l, y)
             scribus.setLineColor(col, line)
             scribus.setLineWidth(0.1, line)

def main():
    root = tk.Tk()
    # High DPI fix windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    
    app = ImpositionApp(root)
    root.mainloop()
    
    try: root.destroy()
    except: pass
    
    # Po zamknięciu okna GUI, uruchamiamy właściwe zadanie w Scribusie
    if app.ready_to_generate:
        app.run_imposition_job()

if __name__ == '__main__':
    main()
