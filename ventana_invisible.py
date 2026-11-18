import sys
import os
import json
import threading
import urllib.request
import urllib.error
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

try:
    from pynput import keyboard as pynput_kbd
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

# Activar DPI Awareness para máxima nitidez en Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Excluye la ventana de Google Meet, Zoom, OBS y grabaciones
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ai_config.json")

CHEAT_SHEET_TEXT = """--- CHULETA RÁPIDA DE ESTRUCTURAS Y LÓGICA (PYTHON / ALGORITMOS) ---

1. LISTAS Y SLICING:
   arr[start:stop:step] | arr[::-1] (invertir) | arr.sort(key=lambda x: x[1])
   comprensión: [x for x in arr if x > 0]
   stack: arr.append(v) / arr.pop() | queue: from collections import deque (popleft())

2. DICCIONARIOS Y SETS:
   from collections import defaultdict, Counter
   frecuencias = Counter(arr)  # Cuenta elementos
   grafo = defaultdict(list)   # Grafo adyacencia
   set: busqueda O(1) -> s.add(v), if x in s:

3. TÉCNICAS CLÁSICAS:
   • Dos Punteros: left, right = 0, len(arr)-1
   • Ventana Deslizante (Sliding Window): expandir right, contraer left
   • Búsqueda Binaria: import bisect (bisect_left, bisect_right)
   • Heap / Cola de prioridad: import heapq (heappush, heappop, heapify)

4. CADENAS (STRINGS):
   s.strip(), s.split(','), ','.join(lista), s.isdigit(), s.lower()
   ord('a') -> 97, chr(97) -> 'a'

5. CASOS LÍMITE (EDGE CASES A REVISAR):
   - ¿Lista vacía? [] o len == 0
   - ¿Un solo elemento?
   - ¿Números negativos o ceros?
   - ¿Elementos duplicados?
   - ¿Entrada nula / None?
"""

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"gemini_api_key": ""}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

class StealthWindowApp:
    def __init__(self, root):
        self.root = root
        # Ocultar root para eliminar completamente el icono de Python de la barra de tareas
        self.root.withdraw()

        # Crear ventana Toplevel como ToolWindow (sin icono en barra de tareas)
        self.win = tk.Toplevel(self.root)
        self.win.title("Panel Invisible Pro")
        self.win.geometry("780x600+100+60")
        self.win.minsize(520, 380)
        self.win.configure(bg="#181825")

        # Quitar de la barra de tareas y Alt+Tab
        self.win.attributes("-toolwindow", True)
        self.win.attributes("-topmost", True)

        self.opacity = tk.DoubleVar(value=0.96)
        self.win.attributes("-alpha", self.opacity.get())

        self.config = load_config()
        self.api_key = self.config.get("gemini_api_key", "")
        self.last_ai_response = ""
        self.font_size = 11

        # PDF Visual
        self.current_pdf_doc = None
        self.current_pdf_page = 0
        self.pdf_zoom = 1.0
        self.pdf_photo_img = None
        self.pdf_mode_visual = True

        self.is_hidden = False
        self.is_compact = False
        self.normal_geometry = "780x600+100+60"

        self._setup_style()
        self._build_ui()
        self._apply_stealth_mode()
        self._setup_global_hotkeys()

        # Atajos de ventana
        self.win.bind("<Control-f>", lambda e: self._toggle_search_bar())
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background="#181825", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4", padding=[14, 7], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#89b4fa")], foreground=[("selected", "#11111b")])

    def _setup_global_hotkeys(self):
        """Atajos globales de teclado con pynput para que funcionen desde cualquier ventana de Windows"""
        if HAS_PYNPUT:
            try:
                self.hotkey_listener = pynput_kbd.GlobalHotKeys({
                    '<f8>': self._safe_toggle_visibility,
                    '<ctrl>+<alt>+h': self._safe_toggle_visibility
                })
                self.hotkey_listener.daemon = True
                self.hotkey_listener.start()
            except Exception:
                pass

    def _safe_toggle_visibility(self):
        self.win.after(0, self.toggle_visibility)

    def _apply_stealth_mode(self):
        """Aplica la exclusion nativa de Windows contra capturas y transmisiones de pantalla"""
        self.win.update_idletasks()
        hwnd = user32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
        
        # Estilo ToolWindow
        style = user32.GetWindowLongW(hwnd, -20)
        style = (style | 0x00000080) & ~0x00040000
        user32.SetWindowLongW(hwnd, -20, style)

        # Excluir de capturas
        res = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        if res:
            self.lbl_status.config(text="🛡️ Modo Invisible Activo (Excluido de Meet/Zoom) | Sin icono", fg="#a6e3a1")
        else:
            self.lbl_status.config(text="⚠️ Modo estándar activo", fg="#f38ba8")

    def _build_ui(self):
        # 1. Barra superior de controles
        top_bar = tk.Frame(self.win, bg="#11111b", height=38, padx=10, pady=5)
        top_bar.pack(side="top", fill="x")

        self.lbl_status = tk.Label(top_bar, text="Iniciando...", font=("Segoe UI", 9, "bold"), bg="#11111b", fg="#89b4fa")
        self.lbl_status.pack(side="left")

        # Opacidad
        lbl_op = tk.Label(top_bar, text="Opacidad:", font=("Segoe UI", 8), bg="#11111b", fg="#a6adc8")
        lbl_op.pack(side="left", padx=(15, 3))
        scale_op = tk.Scale(top_bar, from_=0.35, to=1.0, resolution=0.05, orient="horizontal",
                            variable=self.opacity, command=lambda v: self.win.attributes("-alpha", float(v)),
                            showvalue=False, length=70, bg="#11111b", fg="#89b4fa", highlightthickness=0)
        scale_op.pack(side="left")

        # Botón Modo Compacto / Barra
        self.btn_compact = tk.Button(top_bar, text="🗗 Compacto", command=self._toggle_compact,
                                     bg="#313244", fg="#cdd6f4", activebackground="#45475a",
                                     font=("Segoe UI", 8), relief="flat", padx=6, pady=1)
        self.btn_compact.pack(side="right", padx=3)

        # Botón Ocultar
        btn_panic = tk.Button(top_bar, text="Ocultar (F8)", command=self.toggle_visibility,
                              bg="#313244", fg="#f38ba8", activebackground="#45475a",
                              font=("Segoe UI", 8, "bold"), relief="flat", padx=6, pady=1)
        btn_panic.pack(side="right", padx=3)

        # 2. Contenedor de Pestañas
        self.main_container = tk.Frame(self.win, bg="#181825")
        self.main_container.pack(fill="both", expand=True, padx=6, pady=4)

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill="both", expand=True)

        # Pestaña 1: Asistente IA
        tab_ai = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_ai, text=" 🤖 Asistente IA ")
        self._build_ai_tab(tab_ai)

        # Pestaña 2: Apuntes / Guión con Búsqueda
        tab_notes = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_notes, text=" 📝 Apuntes / Guión ")
        self._build_notes_tab(tab_notes)

        # Pestaña 3: Visor Visual de Documentos / PDFs
        tab_docs = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_docs, text=" 📄 Visor PDFs / Docs ")
        self._build_docs_tab(tab_docs)

        # 3. Barra inferior de estado
        bottom_bar = tk.Frame(self.win, bg="#11111b", height=22, padx=8, pady=2)
        bottom_bar.pack(side="bottom", fill="x")
        lbl_hint = tk.Label(bottom_bar, text="F8: Ocultar/Mostrar Global | Ctrl+F: Buscar en apuntes | Arrastra la ventana desde el borde",
                            font=("Segoe UI", 8), bg="#11111b", fg="#6c7086")
        lbl_hint.pack(side="left")

    def _build_ai_tab(self, parent):
        bar_key = tk.Frame(parent, bg="#1e1e2e", padx=8, pady=4)
        bar_key.pack(fill="x", side="top")

        lbl_k = tk.Label(bar_key, text="Clave API Gemini:", font=("Segoe UI", 8), bg="#1e1e2e", fg="#a6adc8")
        lbl_k.pack(side="left")

        self.entry_key = tk.Entry(bar_key, width=30, font=("Segoe UI", 8), bg="#313244", fg="#cdd6f4",
                                  insertbackground="#89b4fa", show="*")
        self.entry_key.pack(side="left", padx=5)
        if self.api_key:
            self.entry_key.insert(0, self.api_key)

        btn_save_k = tk.Button(bar_key, text="Guardar Clave", command=self._save_api_key,
                               bg="#89b4fa", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=6)
        btn_save_k.pack(side="left", padx=3)

        btn_copy_ans = tk.Button(bar_key, text="📋 Copiar Respuesta", command=self._copy_last_answer,
                                 bg="#313244", fg="#cdd6f4", font=("Segoe UI", 8), relief="flat", padx=6)
        btn_copy_ans.pack(side="right", padx=3)

        btn_clear_chat = tk.Button(bar_key, text="Limpiar", command=self._clear_ai_chat,
                                   bg="#313244", fg="#f38ba8", font=("Segoe UI", 8), relief="flat", padx=6)
        btn_clear_chat.pack(side="right", padx=3)

        frame_chat = tk.Frame(parent, bg="#181825")
        frame_chat.pack(fill="both", expand=True, padx=6, pady=4)

        scroll_chat = tk.Scrollbar(frame_chat)
        scroll_chat.pack(side="right", fill="y")

        self.txt_chat = tk.Text(frame_chat, wrap="word", bg="#181825", fg="#cdd6f4",
                                font=("Segoe UI", 10), padx=8, pady=8, relief="flat",
                                yscrollcommand=scroll_chat.set, state="normal")
        self.txt_chat.pack(side="left", fill="both", expand=True)
        scroll_chat.config(command=self.txt_chat.yview)

        self.txt_chat.tag_configure("user", foreground="#89b4fa", font=("Segoe UI", 10, "bold"))
        self.txt_chat.tag_configure("ai", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.txt_chat.tag_configure("sys", foreground="#a6adc8", font=("Segoe UI", 9, "italic"))

        self._append_chat("sys", "¡Hola! Estoy listo para ayudarte aquí mismo de forma invisible.\n"
                                 "Escribe cualquier duda o pregunta técnica abajo y presiona Enter para recibir una respuesta inmediata.\n")

        bar_input = tk.Frame(parent, bg="#181825", pady=4)
        bar_input.pack(fill="x", side="bottom")

        self.entry_prompt = tk.Entry(bar_input, font=("Segoe UI", 10), bg="#313244", fg="#ffffff",
                                     insertbackground="#89b4fa", relief="flat")
        self.entry_prompt.pack(side="left", fill="x", expand=True, padx=(4, 6), ipady=5)
        self.entry_prompt.bind("<Return>", lambda e: self._send_ai_prompt())

        self.btn_send = tk.Button(bar_input, text="Enviar (Enter)", command=self._send_ai_prompt,
                                  bg="#89b4fa", fg="#11111b", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4)
        self.btn_send.pack(side="right", padx=4)

    def _save_api_key(self):
        k = self.entry_key.get().strip()
        if not k:
            messagebox.showwarning("Aviso", "Ingresa una clave válida.")
            return
        self.api_key = k
        self.config["gemini_api_key"] = k
        save_config(self.config)
        self._append_chat("sys", "✔️ Clave API guardada correctamente. Ya puedes preguntarme lo que quieras.")

    def _copy_last_answer(self):
        if not self.last_ai_response:
            messagebox.showinfo("Aviso", "Aún no hay respuesta para copiar.")
            return
        if HAS_CLIPBOARD:
            pyperclip.copy(self.last_ai_response)
        self.win.clipboard_clear()
        self.win.clipboard_append(self.last_ai_response)
        messagebox.showinfo("Copiado", "Última respuesta copiada al portapapeles.")

    def _clear_ai_chat(self):
        self.txt_chat.delete("1.0", tk.END)
        self._append_chat("sys", "Chat reiniciado. ¿En qué puedo ayudarte?")

    def _append_chat(self, tag, text):
        self.txt_chat.insert(tk.END, text + "\n", tag)
        self.txt_chat.see(tk.END)

    def _send_ai_prompt(self):
        prompt = self.entry_prompt.get().strip()
        if not prompt:
            return

        if not self.api_key:
            self._append_chat("sys", "⚠️ Por favor ingresa tu clave API gratuita de Gemini arriba (aistudio.google.com/app/apikey).")
            return

        self._append_chat("user", f"\nTú: {prompt}")
        self.entry_prompt.delete(0, tk.END)
        self.btn_send.config(state="disabled", text="Pensando...")

        def _worker():
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.6, "maxOutputTokens": 1024}
                }
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=18) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    answer = res_json['candidates'][0]['content']['parts'][0]['text'].strip()

                self.last_ai_response = answer
                self.win.after(0, lambda: self._on_ai_success(answer))
            except Exception as e:
                err_msg = str(e)
                if "400" in err_msg:
                    err_msg = "Clave API inválida o expirada. Verifica en aistudio.google.com"
                self.win.after(0, lambda: self._on_ai_error(err_msg))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ai_success(self, answer):
        self._append_chat("ai", f"Asistente:\n{answer}\n")
        self.btn_send.config(state="normal", text="Enviar (Enter)")

    def _on_ai_error(self, err_msg):
        self._append_chat("sys", f"❌ Error: {err_msg}")
        self.btn_send.config(state="normal", text="Enviar (Enter)")

    def _build_notes_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#181825", pady=3)
        toolbar.pack(fill="x")

        btn_open = tk.Button(toolbar, text="Abrir", command=self._open_text_file,
                             bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=6)
        btn_open.pack(side="left", padx=2)

        btn_save = tk.Button(toolbar, text="Guardar", command=self._save_text_file,
                             bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=6)
        btn_save.pack(side="left", padx=2)

        btn_cheat = tk.Button(toolbar, text="📚 Chuleta Algoritmos", command=self._load_cheat_sheet,
                              bg="#89b4fa", fg="#11111b", relief="flat", font=("Segoe UI", 8, "bold"), padx=6)
        btn_cheat.pack(side="left", padx=(8, 2))

        btn_search = tk.Button(toolbar, text="🔍 Buscar (Ctrl+F)", command=self._toggle_search_bar,
                               bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=6)
        btn_search.pack(side="left", padx=2)

        btn_font_plus = tk.Button(toolbar, text="A+", command=lambda: self._change_font_size(2),
                                  bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8, "bold"), padx=5)
        btn_font_plus.pack(side="left", padx=(8, 2))

        btn_font_minus = tk.Button(toolbar, text="A-", command=lambda: self._change_font_size(-2),
                                   bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8, "bold"), padx=5)
        btn_font_minus.pack(side="left", padx=2)

        btn_clear = tk.Button(toolbar, text="Limpiar", command=lambda: self.txt_notes.delete("1.0", tk.END),
                              bg="#313244", fg="#f38ba8", relief="flat", font=("Segoe UI", 8), padx=6)
        btn_clear.pack(side="right", padx=2)

        # Barra de búsqueda desplegable
        self.frame_search = tk.Frame(parent, bg="#1e1e2e", padx=6, pady=3)
        self.entry_search = tk.Entry(self.frame_search, font=("Segoe UI", 9), bg="#313244", fg="#ffffff",
                                     insertbackground="#89b4fa", width=22)
        self.entry_search.pack(side="left", padx=4)
        self.entry_search.bind("<Return>", lambda e: self._find_in_notes())

        btn_find = tk.Button(self.frame_search, text="Buscar", command=self._find_in_notes,
                             bg="#89b4fa", fg="#11111b", font=("Segoe UI", 8, "bold"), relief="flat", padx=6)
        btn_find.pack(side="left", padx=2)

        self.lbl_search_res = tk.Label(self.frame_search, text="", font=("Segoe UI", 8), bg="#1e1e2e", fg="#a6e3a1")
        self.lbl_search_res.pack(side="left", padx=6)

        frame_text = tk.Frame(parent, bg="#181825")
        frame_text.pack(fill="both", expand=True, pady=3)

        scroll = tk.Scrollbar(frame_text)
        scroll.pack(side="right", fill="y")

        self.txt_notes = tk.Text(frame_text, wrap="word", bg="#1e1e2e", fg="#cdd6f4",
                                 insertbackground="#89b4fa", selectbackground="#45475a",
                                 font=("Segoe UI", self.font_size), padx=8, pady=8,
                                 yscrollcommand=scroll.set, relief="flat", borderwidth=0)
        self.txt_notes.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.txt_notes.yview)

        self.txt_notes.tag_configure("highlight", background="#f9e2af", foreground="#11111b")
        self._load_cheat_sheet()

    def _toggle_search_bar(self):
        if self.frame_search.winfo_ismapped():
            self.frame_search.pack_forget()
            self.txt_notes.tag_remove("highlight", "1.0", tk.END)
        else:
            self.frame_search.pack(fill="x", before=self.txt_notes.master, pady=2)
            self.entry_search.focus_set()

    def _find_in_notes(self):
        query = self.entry_search.get().strip()
        self.txt_notes.tag_remove("highlight", "1.0", tk.END)
        if not query:
            self.lbl_search_res.config(text="")
            return

        count = 0
        idx = "1.0"
        while True:
            idx = self.txt_notes.search(query, idx, nocase=1, stopindex=tk.END)
            if not idx:
                break
            lastidx = f"{idx}+{len(query)}c"
            self.txt_notes.tag_add("highlight", idx, lastidx)
            count += 1
            if count == 1:
                self.txt_notes.see(idx)
            idx = lastidx

        self.lbl_search_res.config(text=f"{count} coincidencia(s)")

    def _load_cheat_sheet(self):
        self.txt_notes.delete("1.0", tk.END)
        self.txt_notes.insert("1.0", CHEAT_SHEET_TEXT)

    def _build_docs_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#181825", pady=3)
        toolbar.pack(fill="x")

        btn_open_doc = tk.Button(toolbar, text="Abrir PDF / Doc", command=self._load_document,
                                 bg="#89b4fa", fg="#11111b", relief="flat", font=("Segoe UI", 8, "bold"), padx=8)
        btn_open_doc.pack(side="left", padx=2)

        self.btn_prev_page = tk.Button(toolbar, text="◀ Anterior", command=lambda: self._turn_pdf_page(-1),
                                       bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=6, state="disabled")
        self.btn_prev_page.pack(side="left", padx=(12, 2))

        self.lbl_page = tk.Label(toolbar, text="Sin documento", bg="#181825", fg="#a6adc8", font=("Segoe UI", 8))
        self.lbl_page.pack(side="left", padx=4)

        self.btn_next_page = tk.Button(toolbar, text="Siguiente ▶", command=lambda: self._turn_pdf_page(1),
                                       bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=6, state="disabled")
        self.btn_next_page.pack(side="left", padx=2)

        # Zoom de PDF
        btn_zoom_in = tk.Button(toolbar, text="🔍+", command=lambda: self._zoom_pdf(0.2),
                                bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=5)
        btn_zoom_in.pack(side="left", padx=(12, 2))

        btn_zoom_out = tk.Button(toolbar, text="🔍-", command=lambda: self._zoom_pdf(-0.2),
                                 bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=5)
        btn_zoom_out.pack(side="left", padx=2)

        # Alternar modo visual / texto
        self.btn_toggle_pdf_mode = tk.Button(toolbar, text="Modo: Visual", command=self._toggle_pdf_view_mode,
                                             bg="#313244", fg="#a6e3a1", relief="flat", font=("Segoe UI", 8), padx=6)
        self.btn_toggle_pdf_mode.pack(side="right", padx=2)

        frame_doc = tk.Frame(parent, bg="#181825")
        frame_doc.pack(fill="both", expand=True, pady=3)

        # Canvas para renderizado visual de página PDF
        self.canvas_pdf = tk.Canvas(frame_doc, bg="#1e1e2e", highlightthickness=0)
        self.scroll_pdf_y = tk.Scrollbar(frame_doc, orient="vertical", command=self.canvas_pdf.yview)
        self.scroll_pdf_x = tk.Scrollbar(frame_doc, orient="horizontal", command=self.canvas_pdf.xview)
        self.canvas_pdf.config(xscrollcommand=self.scroll_pdf_x.set, yscrollcommand=self.scroll_pdf_y.set)

        self.scroll_pdf_y.pack(side="right", fill="y")
        self.scroll_pdf_x.pack(side="bottom", fill="x")
        self.canvas_pdf.pack(side="left", fill="both", expand=True)

        # Texto alternativo para archivos de texto plano
        self.txt_doc = tk.Text(frame_doc, wrap="word", bg="#1e1e2e", fg="#cdd6f4",
                               font=("Segoe UI", 10), padx=8, pady=8, relief="flat", borderwidth=0)

    def _toggle_pdf_view_mode(self):
        if not self.current_pdf_doc:
            return
        self.pdf_mode_visual = not self.pdf_mode_visual
        self.btn_toggle_pdf_mode.config(text="Modo: Visual" if self.pdf_mode_visual else "Modo: Texto")
        self._render_pdf_page()

    def _zoom_pdf(self, delta):
        if not self.current_pdf_doc:
            return
        self.pdf_zoom = max(0.6, min(2.5, self.pdf_zoom + delta))
        self._render_pdf_page()

    def _load_document(self):
        filetypes = [("Documentos", "*.pdf *.txt *.py *.c *.md *.json"), ("Todos", "*.*")]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if not filepath:
            return

        if filepath.lower().endswith(".pdf"):
            if not HAS_PYMUPDF:
                messagebox.showerror("Error", "Se requiere pymupdf para abrir archivos PDF.")
                return
            try:
                self.current_pdf_doc = fitz.open(filepath)
                self.current_pdf_page = 0
                self.pdf_zoom = 1.0
                self._render_pdf_page()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
        else:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                self.canvas_pdf.pack_forget()
                self.txt_doc.pack(side="left", fill="both", expand=True)
                self.txt_doc.delete("1.0", tk.END)
                self.txt_doc.insert("1.0", content)
                self.lbl_page.config(text=os.path.basename(filepath))
                self.btn_prev_page.config(state="disabled")
                self.btn_next_page.config(state="disabled")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

    def _render_pdf_page(self):
        if not self.current_pdf_doc:
            return
        total = len(self.current_pdf_doc)
        page = self.current_pdf_doc[self.current_pdf_page]

        if self.pdf_mode_visual:
            self.txt_doc.pack_forget()
            self.canvas_pdf.pack(side="left", fill="both", expand=True)
            self.canvas_pdf.delete("all")

            # Renderizado visual nativo con PyMuPDF (resolución nítida)
            mat = fitz.Matrix(self.pdf_zoom, self.pdf_zoom)
            pix = page.get_pixmap(matrix=mat)
            ppm_data = pix.tobytes("ppm")
            self.pdf_photo_img = tk.PhotoImage(data=ppm_data)

            self.canvas_pdf.create_image(0, 0, anchor="nw", image=self.pdf_photo_img)
            self.canvas_pdf.config(scrollregion=(0, 0, pix.width, pix.height))
        else:
            self.canvas_pdf.pack_forget()
            self.txt_doc.pack(side="left", fill="both", expand=True)
            self.txt_doc.delete("1.0", tk.END)
            self.txt_doc.insert("1.0", page.get_text())

        self.lbl_page.config(text=f"Página {self.current_pdf_page + 1} de {total} (Zoom: {int(self.pdf_zoom*100)}%)")
        self.btn_prev_page.config(state="normal" if self.current_pdf_page > 0 else "disabled")
        self.btn_next_page.config(state="normal" if self.current_pdf_page < total - 1 else "disabled")

    def _turn_pdf_page(self, delta):
        if not self.current_pdf_doc:
            return
        new_page = self.current_pdf_page + delta
        if 0 <= new_page < len(self.current_pdf_doc):
            self.current_pdf_page = new_page
            self._render_pdf_page()

    def _open_text_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt *.md *.py *.c"), ("Todos", "*.*")])
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    self.txt_notes.delete("1.0", tk.END)
                    self.txt_notes.insert("1.0", f.read())
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir: {e}")

    def _save_text_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self.txt_notes.get("1.0", tk.END))
                messagebox.showinfo("Guardado", "Archivo guardado con éxito.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def _change_font_size(self, delta):
        self.font_size = max(8, min(26, self.font_size + delta))
        self.txt_notes.config(font=("Segoe UI", self.font_size))

    def _toggle_compact(self):
        if not self.is_compact:
            self.normal_geometry = self.win.geometry()
            self.main_container.pack_forget()
            self.win.geometry("380x38")
            self.btn_compact.config(text="🗖 Expandir")
            self.is_compact = True
        else:
            self.win.geometry(self.normal_geometry)
            self.main_container.pack(fill="both", expand=True, padx=6, pady=4)
            self.btn_compact.config(text="🗗 Compacto")
            self.is_compact = False

    def toggle_visibility(self, event=None):
        if self.is_hidden:
            self.win.deiconify()
            self._apply_stealth_mode()
            self.is_hidden = False
        else:
            self.win.withdraw()
            self.is_hidden = True

    def on_close(self):
        self.root.destroy()

def main():
    root = tk.Tk()
    app = StealthWindowApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
