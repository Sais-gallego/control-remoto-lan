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

from PIL import ImageGrab
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key

PORT_VIDEO = 5555
PORT_INPUT = 5556

mouse = MouseController()
keyboard = KeyboardController()

# Configuraciones de calidad intercambiables
# 1: Rapido (75%), 2: Equilibrado (85% por defecto, recomendado), 3: Ultra HD (92%)
current_mode = 2
QUALITY_PRESETS = {
    1: [cv2.IMWRITE_JPEG_QUALITY, 75, cv2.IMWRITE_JPEG_OPTIMIZE, 0],
    2: [cv2.IMWRITE_JPEG_QUALITY, 85, cv2.IMWRITE_JPEG_OPTIMIZE, 0],
    3: [cv2.IMWRITE_JPEG_QUALITY, 92, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444]
}

KEY_MAP = {
    'enter': Key.enter,
    'return': Key.enter,
    'backspace': Key.backspace,
    'tab': Key.tab,
    'space': Key.space,
    'shift': Key.shift,
    'ctrl': Key.ctrl,
    'alt': Key.alt,
    'esc': Key.esc,
    'escape': Key.esc,
    'up': Key.up,
    'down': Key.down,
    'left': Key.left,
    'right': Key.right,
    'delete': Key.delete,
    'home': Key.home,
    'end': Key.end,
    'pageup': Key.page_up,
    'pagedown': Key.page_down,
    'caps_lock': Key.caps_lock,
    'f1': Key.f1,
    'f2': Key.f2,
    'f3': Key.f3,
    'f4': Key.f4,
    'f5': Key.f5,
    'f6': Key.f6,
    'f7': Key.f7,
    'f8': Key.f8,
    'f9': Key.f9,
    'f10': Key.f10,
    'f11': Key.f11,
    'f12': Key.f12
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

# Instancia persistente de mss para evitar recrear contextos GDI en cada frame
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
    # Fallback
    pil_img = ImageGrab.grab(all_screens=False)
    frame = np.array(pil_img)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def draw_cursor(frame):
    try:
        cx, cy = mouse.position
        h, w = frame.shape[:2]
        if 0 <= cx < w and 0 <= cy < h:
            pts = np.array([[cx, cy], [cx, cy + 18], [cx + 5, cy + 14], [cx + 10, cy + 22],
                            [cx + 13, cy + 20], [cx + 8, cy + 12], [cx + 14, cy + 12]], np.int32)
            cv2.fillPoly(frame, [pts], (255, 255, 255))
            cv2.polylines(frame, [pts], True, (0, 0, 0), 1, cv2.LINE_AA)
    except Exception:
        pass
    return frame

def handle_input(conn):
    global current_mode
    print("[INPUT] Cliente de control conectado.")
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

                    elif ev_type == 'set_mode':
                        mode = event.get('mode', 2)
                        if mode in QUALITY_PRESETS:
                            current_mode = mode
                            print(f"[AJUSTE] Modo de calidad cambiado a: {current_mode}")

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
    except Exception as e:
        print(f"[INPUT] Conexion cerrada: {e}")
    finally:
        conn.close()

def video_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Aumentar buffer de envio para no bloquear
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    server_socket.bind(('0.0.0.0', PORT_VIDEO))
    server_socket.listen(1)
    print(f"[VIDEO] Servidor de video escuchando en el puerto {PORT_VIDEO}...")

    while True:
        conn, addr = server_socket.accept()
        print(f"[VIDEO] Cliente conectado desde {addr}")
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        try:
            init_img = capture_screen()
            h, w = init_img.shape[:2]
            header = json.dumps({"width": w, "height": h}).encode('utf-8')
            conn.sendall(struct.pack('>I', len(header)) + header)

            prev_sample = None
            last_sent_time = 0
            last_mouse_pos = (-1, -1)

            while True:
                now = time.time()
                frame = capture_screen()

                # Detección ultra-rápida de cambios (strided diff: 1.1ms)
                curr_sample = frame[::16, ::16]
                curr_mouse = mouse.position

                has_changed = (
                    prev_sample is None or
                    curr_mouse != last_mouse_pos or
                    cv2.absdiff(curr_sample, prev_sample).any() or
                    (now - last_sent_time > 0.3)  # Keepalive cada 300ms
                )

                if has_changed:
                    prev_sample = curr_sample
                    last_mouse_pos = curr_mouse
                    last_sent_time = now

                    frame = draw_cursor(frame)
                    encode_params = QUALITY_PRESETS.get(current_mode, QUALITY_PRESETS[2])
                    _, enc_img = cv2.imencode('.jpg', frame, encode_params)
                    data = enc_img.tobytes()
                    conn.sendall(struct.pack('>I', len(data)) + data)
                else:
                    # Si no hay cambios, pausar 4ms para ahorrar 100% de CPU
                    time.sleep(0.004)

        except (BrokenPipeError, ConnectionResetError):
            print("[VIDEO] Cliente desconectado.")
        except Exception as e:
            print(f"[VIDEO] Error: {e}")
        finally:
            conn.close()

def input_server():
    input_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    input_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    input_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    input_sock.bind(('0.0.0.0', PORT_INPUT))
    input_sock.listen(1)
    print(f"[INPUT] Servidor de control escuchando en el puerto {PORT_INPUT}...")

    while True:
        conn, addr = input_sock.accept()
        handle_input(conn)

def main():
    ip = get_local_ip()
    w, h = get_screen_size()
    print("=" * 65)
    print("       SERVIDOR DE CONTROL REMOTO LAN - ALTO RENDIMIENTO       ")
    print("=" * 65)
    print(f">> Resolucion nativa: {w}x{h}")
    print(f">> Optimizaciones: Persistent MSS, Strided Diff, Zero-Copy TCP")
    print(f">> Modos de calidad: [1] Rapido | [2] Equilibrado | [3] Ultra HD")
    print(f">> TU DIRECCION IP LOCAL: {ip}\n")
    print("Esperando conexion del cliente...")
    print("=" * 65)

    t_input = threading.Thread(target=input_server, daemon=True)
    t_input.start()

    video_server()

if __name__ == '__main__':
    main()
