import socket
import threading
import struct
import json
import time
import sys
import numpy as np
import cv2

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

def capture_screen():
    if HAS_MSS:
        try:
            with mss.mss() as sct:
                mon = sct.monitors[1]
                img = np.array(sct.grab(mon))
                return img[:, :, :3]
        except Exception:
            pass
    # Fallback to ImageGrab
    pil_img = ImageGrab.grab()
    frame = np.array(pil_img)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def handle_input(conn):
    print("[INPUT] Cliente de control conectado.")
    buffer = ""
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
                        screen_w, screen_h = ImageGrab.grab().size
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

                except Exception as e:
                    # Ignorar eventos corruptos
                    pass
    except Exception as e:
        print(f"[INPUT] Conexión cerrada: {e}")
    finally:
        conn.close()

def video_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', PORT_VIDEO))
    server_socket.listen(1)
    print(f"[VIDEO] Servidor de video escuchando en el puerto {PORT_VIDEO}...")

    while True:
        conn, addr = server_socket.accept()
        print(f"[VIDEO] Cliente conectado desde {addr}")
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        try:
            # Enviar primero resolución nativa
            init_img = capture_screen()
            h, w = init_img.shape[:2]
            header = json.dumps({"width": w, "height": h}).encode('utf-8')
            conn.sendall(struct.pack('>I', len(header)) + header)

            while True:
                frame = capture_screen()
                # Codificar JPEG a calidad 75 para máxima velocidad y nitidez
                _, enc_img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                data = enc_img.tobytes()
                # Enviar tamaño (4 bytes) + datos
                conn.sendall(struct.pack('>I', len(data)) + data)
                # Pequeña pausa para no saturar CPU a 60 FPS (~16ms)
                time.sleep(0.016)
        except (BrokenPipeError, ConnectionResetError):
            print("[VIDEO] Cliente desconectado.")
        except Exception as e:
            print(f"[VIDEO] Error: {e}")
        finally:
            conn.close()

def input_server():
    input_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    input_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    input_sock.bind(('0.0.0.0', PORT_INPUT))
    input_sock.listen(1)
    print(f"[INPUT] Servidor de control escuchando en el puerto {PORT_INPUT}...")

    while True:
        conn, addr = input_sock.accept()
        handle_input(conn)

def main():
    ip = get_local_ip()
    print("=" * 60)
    print("       SERVIDOR DE CONTROL REMOTO LAN (PC A MANIPULAR)       ")
    print("=" * 60)
    print(f"\n>> TU DIRECCION IP LOCAL ES: {ip}")
    print(f">> Escribe esta IP en la otra computadora para conectar.\n")
    print("Esperando conexion del cliente...")
    print("Presiona Ctrl + C en esta consola para detener.\n")
    print("=" * 60)

    # Iniciar servidor de input en un hilo
    t_input = threading.Thread(target=input_server, daemon=True)
    t_input.start()

    # Servidor de video en el hilo principal
    video_server()

if __name__ == '__main__':
    main()
