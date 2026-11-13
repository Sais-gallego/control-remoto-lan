import socket
import threading
import struct
import json
import time
import sys
import os
import base64
import ctypes
import tkinter as tk
import winsound
import numpy as np
import cv2

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import pyaudiowpatch as pyaudio
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

from PIL import ImageGrab
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key

PORT_VIDEO = 5555
PORT_INPUT = 5556
PORT_DISCOVERY = 5557
PORT_AUDIO = 5558

user32 = ctypes.windll.user32
mouse = MouseController()
keyboard = KeyboardController()

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Excluir ventana de Google Meet, Zoom, grabaciones

ENCODE_PARAMS = [cv2.IMWRITE_JPEG_QUALITY, 85, cv2.IMWRITE_JPEG_OPTIMIZE, 0]

CURSOR_CODES = {
    'arrow': 0,
    'ibeam': 1,
    'hand': 2,
    'cross': 3,
    'wait': 4,
    'sizens': 5,
    'sizewe': 6,
    'sizenwse': 7,
    'sizenesw': 8,
    'sizeall': 9,
    'no': 10
}

SYSTEM_CURSORS = {}
if HAS_WIN32:
    for name, cid in [
        ('arrow', win32con.IDC_ARROW),
        ('ibeam', win32con.IDC_IBEAM),
        ('hand', win32con.IDC_HAND),
        ('cross', win32con.IDC_CROSS),
        ('wait', win32con.IDC_WAIT),
        ('sizens', win32con.IDC_SIZENS),
        ('sizewe', win32con.IDC_SIZEWE),
        ('sizenwse', win32con.IDC_SIZENWSE),
        ('sizenesw', win32con.IDC_SIZENESW),
        ('sizeall', win32con.IDC_SIZEALL),
        ('no', win32con.IDC_NO),
    ]:
        try:
            h = win32gui.LoadCursor(0, cid)
            if h:
                SYSTEM_CURSORS[h] = name
        except Exception:
            pass

KEY_MAP = {
    'enter': Key.enter,
    'return': Key.enter,
    'backspace': Key.backspace,
    'tab': Key.tab,
    'space': Key.space,
    'shift': Key.shift,
    'left shift': Key.shift_l,
    'right shift': Key.shift_r,
    'ctrl': Key.ctrl,
    'left ctrl': Key.ctrl_l,
    'right ctrl': Key.ctrl_r,
    'alt': Key.alt,
    'left alt': Key.alt_l,
    'right alt': Key.alt_r,
    'alt gr': Key.alt_gr,
    'esc': Key.esc,
    'escape': Key.esc,
    'up': Key.up,
    'down': Key.down,
    'left': Key.left,
    'right': Key.right,
    'delete': Key.delete,
    'insert': Key.insert,
    'home': Key.home,
    'end': Key.end,
    'pageup': Key.page_up,
    'pagedown': Key.page_down,
    'caps_lock': Key.caps_lock,
    'left windows': Key.cmd,
    'right windows': Key.cmd,
    'print screen': Key.print_screen,
    'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
    'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
    'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12
}

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def get_screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def get_active_cursor():
    if not HAS_WIN32:
        return 'arrow'
    try:
        flags, hcur, _ = win32gui.GetCursorInfo()
        if (flags & 1) and hcur:
            if hcur in SYSTEM_CURSORS:
                return SYSTEM_CURSORS[hcur]
            info = win32gui.GetIconInfo(hcur)
            x_hot, y_hot = info[1], info[2]
            win32gui.DeleteObject(info[3])
            if info[4]:
                win32gui.DeleteObject(info[4])
            if 6 <= x_hot <= 10 and 8 <= y_hot <= 14:
                return 'ibeam'
    except Exception:
        pass
    return 'arrow'

sct_instance = None
if HAS_MSS:
    try:
        sct_instance = mss.mss()
    except Exception:
        sct_instance = None

def capture_screen():
    global sct_instance
    if sct_instance is not None:
        try:
            mon = sct_instance.monitors[1]
            img = np.array(sct_instance.grab(mon))
            return img[:, :, :3]
        except Exception:
            pass
    pil_img = ImageGrab.grab(all_screens=False, include_layered_windows=True)
    frame = np.array(pil_img)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def trigger_special_action(action):
    if action == "win_key":
        keyboard.press(Key.cmd)
        keyboard.release(Key.cmd)
    elif action == "alt_tab":
        keyboard.press(Key.alt)
        keyboard.press(Key.tab)
        keyboard.release(Key.tab)
        keyboard.release(Key.alt)
    elif action == "win_tab":
        keyboard.press(Key.cmd)
        keyboard.press(Key.tab)
        keyboard.release(Key.tab)
        keyboard.release(Key.cmd)
    elif action == "show_desktop":
        keyboard.press(Key.cmd)
        keyboard.press('d')
        keyboard.release('d')
        keyboard.release(Key.cmd)

def get_desktop_dir():
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    return desktop if os.path.exists(desktop) else os.path.expanduser('~')

def show_stealth_notification(text):
    """
    Muestra una notificacion flotante discreta en la pantalla fisica.
    Gracias a WDA_EXCLUDEFROMCAPTURE, Google Meet, Zoom o grabadores de pantalla
    NO LA TRANSMITEN (es 100% invisible para los demas en la llamada).
    """
    def _run():
        try:
            # Campanita suave para llamar la atencion del usuario
            winsound.MessageBeep(winsound.MB_ICONASTERISK)

            root = tk.Tk()
            root.withdraw()

            top = tk.Toplevel(root)
            top.overrideredirect(True)
            top.attributes('-topmost', True)
            top.attributes('-alpha', 0.95)
            top.configure(bg='#181825')

            screen_w = top.winfo_screenwidth()
            screen_h = top.winfo_screenheight()
            w, h = 380, 85
            x = screen_w - w - 25
            y = screen_h - h - 70
            top.geometry(f"{w}x{h}+{x}+{y}")

            frame = tk.Frame(top, bg='#181825', padx=14, pady=10)
            frame.pack(fill='both', expand=True)

            lbl_title = tk.Label(
                frame,
                text="💬 Mensaje Privado (Oculto en Meet)",
                font=("Segoe UI", 9, "bold"),
                fg="#89b4fa",
                bg='#181825'
            )
            lbl_title.pack(anchor='w')

            lbl_msg = tk.Label(
                frame,
                text=text,
                font=("Segoe UI", 11),
                fg="#cdd6f4",
                bg='#181825',
                wraplength=350,
                justify='left'
            )
            lbl_msg.pack(anchor='w', pady=(4, 0))

            top.update_idletasks()
            hwnd = user32.GetParent(top.winfo_id()) or top.winfo_id()
            # Aplicar exclusion de captura para que Meet no lo muestre
            user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

            # Clic para descartar
            for widget in (top, frame, lbl_title, lbl_msg):
                widget.bind("<Button-1>", lambda e: root.destroy())

            # Autocierre en 6.5 segundos
            top.after(6500, root.destroy)
            root.mainloop()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()

def handle_input(conn):
    buffer = ""
    screen_w, screen_h = get_screen_size()
    current_receiving_file = None
    last_clipboard = ""

    def clipboard_sender():
        nonlocal last_clipboard
        if not HAS_CLIPBOARD:
            return
        while True:
            try:
                text = pyperclip.paste()
                if text and text != last_clipboard:
                    last_clipboard = text
                    msg = json.dumps({"type": "clipboard", "text": text}) + '\n'
                    conn.sendall(msg.encode('utf-8'))
            except Exception:
                break
            time.sleep(0.4)

    t_clip = threading.Thread(target=clipboard_sender, daemon=True)
    t_clip.start()

    try:
        while True:
            data = conn.recv(65536)
            if not data:
                break
            buffer += data.decode('utf-8', errors='ignore')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    ev_type = event.get('type')

                    if ev_type == 'mouse_move':
                        nx, ny = event['x'], event['y']
                        target_x = int(nx * screen_w)
                        target_y = int(ny * screen_h)
                        
                        user32.SetCursorPos(target_x, target_y)
                        norm_x = int(nx * 65535)
                        norm_y = int(ny * 65535)
                        user32.mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, norm_x, norm_y, 0, 0)

                    elif ev_type == 'mouse_down':
                        btn = event.get('button')
                        if btn == 1:
                            mouse.press(Button.left)
                        elif btn == 3:
                            mouse.press(Button.right)
                        elif btn == 2:
                            mouse.press(Button.middle)

                    elif ev_type == 'mouse_up':
                        btn = event.get('button')
                        if btn == 1:
                            mouse.release(Button.left)
                        elif btn == 3:
                            mouse.release(Button.right)
                        elif btn == 2:
                            mouse.release(Button.middle)

                    elif ev_type == 'mouse_scroll':
                        dy = event.get('dy', 0)
                        mouse.scroll(0, dy)

                    elif ev_type == 'special_action':
                        action = event.get('action')
                        trigger_special_action(action)

                    elif ev_type == 'private_chat':
                        chat_text = event.get('text', '')
                        if chat_text:
                            show_stealth_notification(chat_text)

                    elif ev_type == 'clipboard':
                        text = event.get('text', '')
                        if HAS_CLIPBOARD and text:
                            last_clipboard = text
                            pyperclip.copy(text)

                    elif ev_type == 'file_start':
                        fname = os.path.basename(event.get('filename', 'archivo_recibido'))
                        target_dir = get_desktop_dir()
                        target_path = os.path.join(target_dir, fname)
                        
                        base, ext = os.path.splitext(target_path)
                        counter = 1
                        while os.path.exists(target_path):
                            target_path = f"{base} ({counter}){ext}"
                            counter += 1

                        current_receiving_file = open(target_path, 'wb')

                    elif ev_type == 'file_chunk':
                        if current_receiving_file:
                            raw_bytes = base64.b64decode(event.get('data', ''))
                            current_receiving_file.write(raw_bytes)

                    elif ev_type == 'file_end':
                        if current_receiving_file:
                            current_receiving_file.close()
                            current_receiving_file = None

                    elif ev_type == 'key_down':
                        key_str = event.get('key', '').lower()
                        char = event.get('char')
                        if key_str in KEY_MAP:
                            keyboard.press(KEY_MAP[key_str])
                        elif char:
                            try:
                                keyboard.press(char)
                            except Exception:
                                pass

                    elif ev_type == 'key_up':
                        key_str = event.get('key', '').lower()
                        char = event.get('char')
                        if key_str in KEY_MAP:
                            keyboard.release(KEY_MAP[key_str])
                        elif char:
                            try:
                                keyboard.release(char)
                            except Exception:
                                pass

                except Exception:
                    pass
    except Exception:
        pass
    finally:
        if current_receiving_file:
            try:
                current_receiving_file.close()
            except Exception:
                pass
        conn.close()

def video_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    server_socket.bind(('0.0.0.0', PORT_VIDEO))
    server_socket.listen(1)

    while True:
        conn, addr = server_socket.accept()
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        try:
            init_img = capture_screen()
            h, w = init_img.shape[:2]
            header = json.dumps({"width": w, "height": h}).encode('utf-8')
            conn.sendall(struct.pack('>I', len(header)) + header)

            prev_sample = None
            last_sent_time = 0
            last_mouse_pos = (-1, -1)
            last_cursor_code = -1

            while True:
                now = time.time()
                frame = capture_screen()

                curr_sample = frame[::8, ::8]
                curr_mouse = mouse.position
                cur_name = get_active_cursor()
                cur_code = CURSOR_CODES.get(cur_name, 0)
                is_on_taskbar = (curr_mouse[1] >= (h - 70))

                has_changed = (
                    prev_sample is None or
                    curr_mouse != last_mouse_pos or
                    cur_code != last_cursor_code or
                    is_on_taskbar or
                    cv2.absdiff(curr_sample, prev_sample).any() or
                    (now - last_sent_time > 0.25)
                )

                if has_changed:
                    prev_sample = curr_sample
                    last_mouse_pos = curr_mouse
                    last_cursor_code = cur_code
                    last_sent_time = now

                    _, enc_img = cv2.imencode('.jpg', frame, ENCODE_PARAMS)
                    data = enc_img.tobytes()

                    hdr = struct.pack('>IB', len(data), cur_code)
                    conn.sendall(hdr + data)
                else:
                    time.sleep(0.004)

        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            pass
        finally:
            conn.close()

def audio_server():
    if not HAS_AUDIO:
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind(('0.0.0.0', PORT_AUDIO))
        server_socket.listen(1)
    except Exception:
        return

    while True:
        try:
            conn, addr = server_socket.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            p = pyaudio.PyAudio()
            try:
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_speakers = p.get_device_info_by_index(wasapi_info['defaultOutputDevice'])

                if not default_speakers['isLoopbackDevice']:
                    for loopback in p.get_loopback_device_info_generator():
                        if default_speakers['name'] in loopback['name']:
                            default_speakers = loopback
                            break
                    else:
                        default_speakers = p.get_default_wasapi_loopback()

                sample_rate = int(default_speakers['defaultSampleRate'])
                channels = min(2, int(default_speakers['maxInputChannels']))

                audio_hdr = json.dumps({"rate": sample_rate, "channels": channels}).encode('utf-8')
                conn.sendall(struct.pack('>I', len(audio_hdr)) + audio_hdr)

                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    input_device_index=default_speakers['index'],
                    frames_per_buffer=1024
                )

                while True:
                    data = stream.read(1024, exception_on_overflow=False)
                    conn.sendall(struct.pack('>I', len(data)) + data)

            except Exception:
                pass
            finally:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
                p.terminate()
                conn.close()
        except Exception:
            pass

def input_server():
    input_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    input_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    input_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    input_sock.bind(('0.0.0.0', PORT_INPUT))
    input_sock.listen(1)

    while True:
        conn, addr = input_sock.accept()
        handle_input(conn)

def discovery_broadcaster(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = json.dumps({"app": "remote_lan_desk", "ip": ip}).encode('utf-8')
    while True:
        try:
            sock.sendto(msg, ('<broadcast>', PORT_DISCOVERY))
        except Exception:
            pass
        time.sleep(1.0)

def show_startup_notification(ip):
    try:
        msg = f"Servidor de Control Remoto iniciado en segundo plano.\n\nIP de esta PC: {ip}\nAudio y Chat Privado (Invisible en Meet): Activados\n\nPara detener el servicio cuando termines, ejecuta 'DETENER_SERVIDOR.bat'."
        ctypes.windll.user32.MessageBoxW(0, msg, "Control Remoto LAN - Activo", 0x40 | 0x10000)
    except Exception:
        pass

def main():
    ip = get_local_ip()

    t_disc = threading.Thread(target=discovery_broadcaster, args=(ip,), daemon=True)
    t_disc.start()

    t_input = threading.Thread(target=input_server, daemon=True)
    t_input.start()

    t_audio = threading.Thread(target=audio_server, daemon=True)
    t_audio.start()

    t_notify = threading.Thread(target=show_startup_notification, args=(ip,), daemon=True)
    t_notify.start()

    video_server()

if __name__ == '__main__':
    main()
