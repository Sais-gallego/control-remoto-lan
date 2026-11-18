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
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

# Activar DPI Awareness para máxima nitidez en Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Excluye la ventana de Google Meet, Zoom, OBS y grabadores de pantalla
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ai_config.json")

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

        # Crear ventana Toplevel como ventana de herramientas (ToolWindow)
        # Esto garantiza que NO aparezca en la barra de tareas ni en Alt+Tab
        self.win = tk.Toplevel(self.root)
        self.win.title("Ventana Invisible")
        self.win.geometry("720x560+120+80")
        self.win.minsize(480, 350)
        self.win.configure(bg="#181825")

        # Quitar icono de la barra de tareas de Windows (WS_EX_TOOLWINDOW)
        self.win.attributes("-toolwindow", True)
        self.win.attributes("-topmost", True)

        self.opacity = tk.DoubleVar(value=0.96)
        self.win.attributes("-alpha", self.opacity.get())

        self.config = load_config()
        self.api_key = self.config.get("gemini_api_key", "")
        self.last_ai_response = ""
        self.font_size = 11

        self.current_pdf_doc = None
        self.current_pdf_page = 0
        self.is_hidden = False

        self._setup_style()
        self._build_ui()
        self._apply_stealth_mode()

        # Atajos globales de visibilidad
        self.win.bind("<F8>", self.toggle_visibility)
        self.win.bind("<Control-h>", self.toggle_visibility)

        # Cuando se cierre la ventana, cerrar la aplicación completa
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background="#181825", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4", padding=[14, 7], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#89b4fa")], foreground=[("selected", "#11111b")])

    def _apply_stealth_mode(self):
        """Aplica la exclusion nativa de Windows contra capturas y transmisiones de pantalla"""
        self.win.update_idletasks()
        hwnd = user32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
        
        # Aplicar estilo de ventana flotante sin barra de tareas adicional
        style = user32.GetWindowLongW(hwnd, -20)
        style = (style | 0x00000080) & ~0x00040000  # WS_EX_TOOLWINDOW activo, WS_EX_APPWINDOW inactivo
        user32.SetWindowLongW(hwnd, -20, style)

        # Excluir de Google Meet, Zoom, grabaciones y capturas
        res = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        if res:
            self.lbl_status.config(text="🛡️ Invisible en Google Meet | Sin icono en barra de tareas", fg="#a6e3a1")
        else:
            self.lbl_status.config(text="⚠️ Modo estándar activo", fg="#f38ba8")

    def _build_ui(self):
        # Barra superior compacta
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

        # Botón Ocultar
        btn_panic = tk.Button(top_bar, text="Ocultar (F8)", command=self.toggle_visibility,
                              bg="#313244", fg="#f38ba8", activebackground="#45475a",
                              font=("Segoe UI", 8, "bold"), relief="flat", padx=6, pady=1)
        btn_panic.pack(side="right")

        # Pestañas principales
        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # 1. Pestaña: Chat IA (Hablar con el Asistente directamente aquí)
        tab_ai = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_ai, text=" 🤖 Asistente IA ")
        self._build_ai_tab(tab_ai)

        # 2. Pestaña: Bloc de Apuntes / Guion
        tab_notes = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_notes, text=" 📝 Apuntes / Guión ")
        self._build_notes_tab(tab_notes)

        # 3. Pestaña: Visor de Documentos / PDFs
        tab_docs = tk.Frame(self.notebook, bg="#181825")
        self.notebook.add(tab_docs, text=" 📄 Visor Documentos ")
        self._build_docs_tab(tab_docs)

        # Barra inferior informativa
        bottom_bar = tk.Frame(self.win, bg="#11111b", height=22, padx=8, pady=2)
        bottom_bar.pack(side="bottom", fill="x")
        lbl_hint = tk.Label(bottom_bar, text="Pantalla limpia en Meet | Barra de tareas sin iconos | Presiona F8 para ocultar",
                            font=("Segoe UI", 8), bg="#11111b", fg="#6c7086")
        lbl_hint.pack(side="left")

    def _build_ai_tab(self, parent):
        # Barra de configuración de API Key
        bar_key = tk.Frame(parent, bg="#1e1e2e", padx=8, pady=4)
        bar_key.pack(fill="x", side="top")

        lbl_k = tk.Label(bar_key, text="Clave API Gemini:", font=("Segoe UI", 8), bg="#1e1e2e", fg="#a6adc8")
        lbl_k.pack(side="left")

        self.entry_key = tk.Entry(bar_key, width=32, font=("Segoe UI", 8), bg="#313244", fg="#cdd6f4",
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

        btn_clear_chat = tk.Button(bar_key, text="Limpiar Chat", command=self._clear_ai_chat,
                                   bg="#313244", fg="#f38ba8", font=("Segoe UI", 8), relief="flat", padx=6)
        btn_clear_chat.pack(side="right", padx=3)

        # Historial de conversación
        frame_chat = tk.Frame(parent, bg="#181825")
        frame_chat.pack(fill="both", expand=True, padx=6, pady=4)

        scroll_chat = tk.Scrollbar(frame_chat)
        scroll_chat.pack(side="right", fill="y")

        self.txt_chat = tk.Text(frame_chat, wrap="word", bg="#181825", fg="#cdd6f4",
                                font=("Segoe UI", 10), padx=8, pady=8, relief="flat",
                                yscrollcommand=scroll_chat.set, state="normal")
        self.txt_chat.pack(side="left", fill="both", expand=True)
        scroll_chat.config(command=self.txt_chat.yview)

        # Configurar colores de mensajes
        self.txt_chat.tag_configure("user", foreground="#89b4fa", font=("Segoe UI", 10, "bold"))
        self.txt_chat.tag_configure("ai", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.txt_chat.tag_configure("sys", foreground="#a6adc8", font=("Segoe UI", 9, "italic"))

        # Mensaje de bienvenida
        self._append_chat("sys", "¡Hola! Estoy listo para ayudarte aquí mismo de forma invisible.\n"
                                 "Puedes hacerme cualquier pregunta, pedirme respuestas, resúmenes o explicaciones durante tu reunión o clase.\n"
                                 "(Si aún no tienes una clave gratuita de Gemini, puedes obtenerla en https://aistudio.google.com/app/apikey y guardarla arriba).\n")

        # Barra de entrada de mensaje
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
            self._append_chat("sys", "⚠️ Por favor ingresa y guarda tu clave API de Gemini en la barra superior para responderte.\n"
                                     "Puedes conseguir una 100% gratuita en: https://aistudio.google.com/app/apikey")
            return

        self._append_chat("user", f"\nTú: {prompt}")
        self.entry_prompt.delete(0, tk.END)
        self.btn_send.config(state="disabled", text="Pensando...")

        def _worker():
            try:
                # Usar Gemini 2.0 Flash o 1.5 Flash directamente mediante endpoint oficial
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024}
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
                    err_msg = "Clave API inválida o expirada. Verifica tu clave en aistudio.google.com"
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

        btn_open = tk.Button(toolbar, text="Abrir Archivo", command=self._open_text_file,
                             bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=6)
        btn_open.pack(side="left", padx=2)

        btn_save = tk.Button(toolbar, text="Guardar", command=self._save_text_file,
                             bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8), padx=6)
        btn_save.pack(side="left", padx=2)

        btn_font_plus = tk.Button(toolbar, text="A+", command=lambda: self._change_font_size(2),
                                  bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8, "bold"), padx=5)
        btn_font_plus.pack(side="left", padx=(10, 2))

        btn_font_minus = tk.Button(toolbar, text="A-", command=lambda: self._change_font_size(-2),
                                   bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 8, "bold"), padx=5)
        btn_font_minus.pack(side="left", padx=2)

        btn_clear = tk.Button(toolbar, text="Limpiar", command=lambda: self.txt_notes.delete("1.0", tk.END),
                              bg="#313244", fg="#f38ba8", relief="flat", font=("Segoe UI", 8), padx=6)
        btn_clear.pack(side="right", padx=2)

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

        welcome_msg = (
            "--- BLOC DE NOTAS INVISIBLE ---\n\n"
            "• Pega aquí tu guión, apuntes o respuestas.\n"
            "• En Google Meet tu pantalla se ve completamente limpia.\n"
            "• En la barra de tareas de Windows NO aparece ningún icono.\n"
            "• Presiona F8 para ocultar o mostrar la ventana al instante.\n"
        )
        self.txt_notes.insert("1.0", welcome_msg)

    def _build_docs_tab(self, parent):
        toolbar = tk.Frame(parent, bg="#181825", pady=3)
        toolbar.pack(fill="x")

        btn_open_doc = tk.Button(toolbar, text="Cargar PDF o Archivo", command=self._load_document,
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

        frame_doc = tk.Frame(parent, bg="#181825")
        frame_doc.pack(fill="both", expand=True, pady=3)

        scroll_doc = tk.Scrollbar(frame_doc)
        scroll_doc.pack(side="right", fill="y")

        self.txt_doc = tk.Text(frame_doc, wrap="word", bg="#1e1e2e", fg="#cdd6f4",
                               font=("Segoe UI", 10), padx=8, pady=8,
                               yscrollcommand=scroll_doc.set, relief="flat", borderwidth=0)
        self.txt_doc.pack(side="left", fill="both", expand=True)
        scroll_doc.config(command=self.txt_doc.yview)

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
        self.font_size = max(8, min(26, self.font_size + delta))
        self.txt_notes.config(font=("Segoe UI", self.font_size))

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
