import socket
import threading
import struct
import json
import time
import sys
import ctypes
import numpy as np
import cv2

# Activar DPI Awareness
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

from PIL import ImageGrab
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key

PORT_VIDEO = 5555
PORT_INPUT = 5556
PORT_DISCOVERY = 5557

mouse = MouseController()
keyboard = KeyboardController()

# Modo unico equilibrado: rapido, nitido y sin complicaciones
ENCODE_PARAMS = [cv2.IMWRITE_JPEG_QUALITY, 85, cv2.IMWRITE_JPEG_OPTIMIZE, 0]

# Codigos de cursores nativos sincronizados
CURSOR_CODES = {
    'arrow': 0,
    'ibeam': 1,      # Texto / input / punto de insercion
    'hand': 2,       # Enlaces / botones clickeables
    'cross': 3,      # Cruz
    'wait': 4,       # Espera
    'sizens': 5,     # Redimensionar vertical
    'sizewe': 6,     # Redimensionar horizontal
    'sizenwse': 7,   # Redimensionar diagonal 1
    'sizenesw': 8,   # Redimensionar diagonal 2
    'sizeall': 9,    # Mover ventana
    'no': 10         # Prohibido
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
    user32 = ctypes.windll.user32
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
    pil_img = ImageGrab.grab(all_screens=False)
    frame = np.array(pil_img)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def handle_input(conn):
    buffer = ""
    screen_w, screen_h = get_screen_size()
    try:
        while True:
            data = conn.recv(4096)
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
                        mouse.position = (target_x, target_y)

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

                curr_sample = frame[::16, ::16]
                curr_mouse = mouse.position
                cur_name = get_active_cursor()
                cur_code = CURSOR_CODES.get(cur_name, 0)

                has_changed = (
                    prev_sample is None or
                    curr_mouse != last_mouse_pos or
                    cur_code != last_cursor_code or
                    cv2.absdiff(curr_sample, prev_sample).any() or
                    (now - last_sent_time > 0.3)
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
    # Emite presencia en la red local para que el cliente detecte la IP automáticamente
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
    # Aviso informativo sin terminal que no interrumpe y se cierra al aceptar
    try:
        msg = f"Servidor de Control Remoto iniciado en segundo plano.\n\nIP de esta PC: {ip}\n\nPara detener el servicio cuando termines, ejecuta 'DETENER_SERVIDOR.bat'."
        ctypes.windll.user32.MessageBoxW(0, msg, "Control Remoto LAN - Activo", 0x40 | 0x10000)
    except Exception:
        pass

def main():
    ip = get_local_ip()

    # Iniciar hilo de auto-deteccion en la red LAN
    t_disc = threading.Thread(target=discovery_broadcaster, args=(ip,), daemon=True)
    t_disc.start()

    # Iniciar servidor de input
    t_input = threading.Thread(target=input_server, daemon=True)
    t_input.start()

    # Notificacion nativa de inicio (hilo separado para no bloquear)
    t_notify = threading.Thread(target=show_startup_notification, args=(ip,), daemon=True)
    t_notify.start()

    # Servidor de video en bucle principal
    video_server()

if __name__ == '__main__':
    main()
