import sys
import os
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

# Activar DPI Awareness para que los textos se vean 100% nítidos en pantallas modernas
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Excluye la ventana de Google Meet, Zoom, Teams, OBS y grabaciones

class StealthWindowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ventana Invisible (Oculta en Google Meet)")
        self.root.geometry("680x520+150+120")
        self.root.minsize(450, 320)
        self.root.configure(bg="#181825")

        # Variables de estado
        self.always_on_top = tk.BooleanVar(value=True)
        self.hide_from_taskbar = tk.BooleanVar(value=False)
        self.opacity = tk.DoubleVar(value=0.96)
        self.font_size = 12
        self.current_pdf_doc = None
        self.current_pdf_page = 0

        # Aplicar siempre encima
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.opacity.get())

        self._setup_style()
        self._build_ui()
        self._apply_stealth_mode()

        # Atajo global de pánico para ocultar/mostrar (F8 o Ctrl+H)
        self.root.bind("<F8>", self.toggle_visibility)
        self.root.bind("<Control-h>", self.toggle_visibility)
        self.is_hidden = False

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background="#181825", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4", padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#89b4fa")], foreground=[("selected", "#11111b")])

    def _apply_stealth_mode(self):
        """Aplica la exclusion nativa de Windows contra capturas y transmisiones de pantalla"""
        self.root.update_idletasks()
        hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
        res = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        if res:
            self.lbl_status.config(text="🛡️ Modo Invisible Activo (Google Meet / Zoom no ven esta ventana)", fg="#a6e3a1")
        else:
            self.lbl_status.config(text="⚠️ Advertencia: No se pudo aplicar exclusion de captura", fg="#f38ba8")

    def _build_ui(self):
        # Barra superior con controles de sigilo y estado
        top_bar = tk.Frame(self.root, bg="#11111b", height=42, padx=10, pady=6)
        top_bar.pack(side="top", fill="x")

        self.lbl_status = tk.Label(top_bar, text="Activando Modo Invisible...", font=("Segoe UI", 9, "bold"), bg="#11111b", fg="#89b4fa")
        self.lbl_status.pack(side="left")

        # Control de transparencia
        lbl_op = tk.Label(top_bar, text="Opacidad:", font=("Segoe UI", 9), bg="#11111b", fg="#a6adc8")
        lbl_op.pack(side="left", padx=(15, 4))
        scale_op = tk.Scale(top_bar, from_=0.35, to=1.0, resolution=0.05, orient="horizontal",
                            variable=self.opacity, command=self._on_opacity_change,
                            showvalue=False, length=80, bg="#11111b", fg="#89b4fa", highlightthickness=0)
        scale_op.pack(side="left")

        # Botón Siempre Encima
        chk_top = tk.Checkbutton(top_bar, text="Fijar Arriba", variable=self.always_on_top,
                                 command=self._on_top_toggle, bg="#11111b", fg="#cdd6f4",
                                 selectcolor="#181825", activebackground="#11111b", activeforeground="#89b4fa",
                                 font=("Segoe UI", 9))
        chk_top.pack(side="left", padx=10)

        # Botón Ayuda / Ocultar
        btn_panic = tk.Button(top_bar, text="Ocultar (F8)", command=self.toggle_visibility,
                              bg="#313244", fg="#f38ba8", activebackground="#45475a",
                              font=("Segoe UI", 8, "bold"), relief="flat", padx=8, pady=2)
        btn_panic.pack(side="right")

        # Cuaderno de Pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Pestaña 1: Bloc de Apuntes / Guión / Respuestas
        tab_notes = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_notes, text=" 📝 Apuntes / Guión ")
        self._build_notes_tab(tab_notes)

        # Pestaña 2: Visor de Documentos / PDFs
        tab_docs = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_docs, text=" 📄 Visor Documentos ")
        self._build_docs_tab(tab_docs)

        # Barra inferior informativa
        bottom_bar = tk.Frame(self.root, bg="#11111b", height=24, padx=10, pady=3)
        bottom_bar.pack(side="bottom", fill="x")
        lbl_hint = tk.Label(bottom_bar, text="Para ti es visible y usable | En la llamada de Meet la pantalla se ve 100% limpia",
                            font=("Segoe UI", 8), bg="#11111b", fg="#6c7086")
        lbl_hint.pack(side="left")

    def _build_notes_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#181825", pady=4)
        toolbar.pack(fill="x")

        btn_open = tk.Button(toolbar, text="Abrir Archivo", command=self._open_text_file,
                             bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 9), padx=6)
        btn_open.pack(side="left", padx=2)

        btn_save = tk.Button(toolbar, text="Guardar", command=self._save_text_file,
                             bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 9), padx=6)
        btn_save.pack(side="left", padx=2)

        btn_font_plus = tk.Button(toolbar, text="A+", command=lambda: self._change_font_size(2),
                                  bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 9, "bold"), padx=6)
        btn_font_plus.pack(side="left", padx=(10, 2))

        btn_font_minus = tk.Button(toolbar, text="A-", command=lambda: self._change_font_size(-2),
                                   bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 9, "bold"), padx=6)
        btn_font_minus.pack(side="left", padx=2)

        btn_clear = tk.Button(toolbar, text="Limpiar", command=lambda: self.txt_notes.delete("1.0", tk.END),
                              bg="#313244", fg="#f38ba8", relief="flat", font=("Segoe UI", 9), padx=6)
        btn_clear.pack(side="right", padx=2)

        # Área de texto
        frame_text = tk.Frame(parent, bg="#181825")
        frame_text.pack(fill="both", expand=True, pady=4)

        scroll = tk.Scrollbar(frame_text)
        scroll.pack(side="right", fill="y")

        self.txt_notes = tk.Text(frame_text, wrap="word", bg="#1e1e2e", fg="#cdd6f4",
                                 insertbackground="#89b4fa", selectbackground="#45475a",
                                 font=("Segoe UI", self.font_size), padx=10, pady=10,
                                 yscrollcommand=scroll.set, relief="flat", borderwidth=0)
        self.txt_notes.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.txt_notes.yview)

        # Mensaje de bienvenida de muestra
        welcome_msg = (
            "--- BLOC DE NOTAS INVISIBLE ---\n\n"
            "Puedes pegar aquí tu guión, preguntas de examen, respuestas o notas de la reunión.\n"
            "Esta ventana está protegida con WDA_EXCLUDEFROMCAPTURE:\n"
            "• Quien esté en tu llamada de Google Meet NO verá nada de lo que tengas aquí escrito.\n"
            "• Para ti está aquí presente; puedes moverla, escribir y leer cómodamente.\n"
            "• Presiona F8 para ocultarla o mostrarla en cualquier segundo.\n"
        )
        self.txt_notes.insert("1.0", welcome_msg)

    def _build_docs_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#181825", pady=4)
        toolbar.pack(fill="x")

        btn_open_doc = tk.Button(toolbar, text="Cargar PDF o Documento", command=self._load_document,
                                 bg="#89b4fa", fg="#11111b", relief="flat", font=("Segoe UI", 9, "bold"), padx=8)
        btn_open_doc.pack(side="left", padx=2)

        self.btn_prev_page = tk.Button(toolbar, text="◀ Anterior", command=lambda: self._turn_pdf_page(-1),
                                       bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 9), padx=6, state="disabled")
        self.btn_prev_page.pack(side="left", padx=(15, 2))

        self.lbl_page = tk.Label(toolbar, text="Sin documento", bg="#181825", fg="#a6adc8", font=("Segoe UI", 9))
        self.lbl_page.pack(side="left", padx=4)

        self.btn_next_page = tk.Button(toolbar, text="Siguiente ▶", command=lambda: self._turn_pdf_page(1),
                                       bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 9), padx=6, state="disabled")
        self.btn_next_page.pack(side="left", padx=2)

        frame_doc = tk.Frame(parent, bg="#181825")
        frame_doc.pack(fill="both", expand=True, pady=4)

        scroll_doc = tk.Scrollbar(frame_doc)
        scroll_doc.pack(side="right", fill="y")

        self.txt_doc = tk.Text(frame_doc, wrap="word", bg="#1e1e2e", fg="#cdd6f4",
                               font=("Segoe UI", 11), padx=10, pady=10,
                               yscrollcommand=scroll_doc.set, relief="flat", borderwidth=0)
        self.txt_doc.pack(side="left", fill="both", expand=True)
        scroll_doc.config(command=self.txt_doc.yview)

    def _load_document(self):
        filetypes = [("Documentos", "*.pdf *.txt *.py *.c *.md *.json"), ("Todos los archivos", "*.*")]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if not filepath:
            return

        if filepath.lower().endswith(".pdf"):
            if not HAS_PYMUPDF:
                messagebox.showerror("Error", "Para leer PDFs se requiere pymupdf (instalado en el sistema)")
                return
            try:
                self.current_pdf_doc = pymupdf.open(filepath)
                self.current_pdf_page = 0
                self._render_pdf_page()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
        else:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
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
        text = page.get_text()

        self.txt_doc.delete("1.0", tk.END)
        self.txt_doc.insert("1.0", text)
        self.lbl_page.config(text=f"Página {self.current_pdf_page + 1} de {total}")

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
        self.font_size = max(8, min(28, self.font_size + delta))
        self.txt_notes.config(font=("Segoe UI", self.font_size))

    def _on_opacity_change(self, val):
        self.root.attributes("-alpha", float(val))

    def _on_top_toggle(self):
        self.root.attributes("-topmost", self.always_on_top.get())

    def toggle_visibility(self, event=None):
        if self.is_hidden:
            self.root.deiconify()
            self._apply_stealth_mode()
            self.is_hidden = False
        else:
            self.root.withdraw()
            self.is_hidden = True

def main():
    root = tk.Tk()
    app = StealthWindowApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
