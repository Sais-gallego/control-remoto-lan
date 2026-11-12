import socket
import struct
import json
import threading
import time
import sys
import os
import ctypes
import cv2
import numpy as np

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame

PORT_VIDEO = 5555
PORT_INPUT = 5556
PORT_DISCOVERY = 5557

def recv_all(sock, size):
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)

def auto_discover_server(timeout=1.2):
    # Escucha la red local para detectar la otra PC automáticamente
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    detected_ip = None
    try:
        sock.bind(('', PORT_DISCOVERY))
        data, addr = sock.recvfrom(1024)
        info = json.loads(data.decode('utf-8'))
        if info.get('app') == 'remote_lan_desk':
            detected_ip = info.get('ip', addr[0])
    except Exception:
        pass
    finally:
        sock.close()
    return detected_ip

def main():
    print("=" * 65)
    print("              CLIENTE DE CONTROL REMOTO LAN                  ")
    print("=" * 65)

    server_ip = None
    if len(sys.argv) > 1:
        server_ip = sys.argv[1].strip()
    else:
        print("Buscando computadora en la red local...")
        discovered_ip = auto_discover_server(timeout=1.2)
        if discovered_ip:
            print(f">> ¡Computadora detectada en la red!: {discovered_ip}")
            choice = input(f"Presiona Enter para conectar a [{discovered_ip}] o escribe otra IP: ").strip()
            server_ip = choice if choice else discovered_ip
        else:
            server_ip = input("Ingresa la direccion IP de la PC a manipular: ").strip()

    if not server_ip:
        print("Direccion IP invalida.")
        return

    print(f"\nConectando a {server_ip}...")

    try:
        video_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        video_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        video_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        video_sock.connect((server_ip, PORT_VIDEO))

        input_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        input_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        input_sock.connect((server_ip, PORT_INPUT))
        print("¡Conexion establecida con exito!")
    except Exception as e:
        print(f"Error al conectar con la PC destino: {e}")
        input("Presiona Enter para salir...")
        return

    # Recibir resolución original del servidor
    hdr_len_bytes = recv_all(video_sock, 4)
    if not hdr_len_bytes:
        print("No se pudo recibir configuracion de pantalla.")
        return
    hdr_len = struct.unpack('>I', hdr_len_bytes)[0]
    hdr_data = recv_all(video_sock, hdr_len)
    info = json.loads(hdr_data.decode('utf-8'))
    native_w, native_h = info['width'], info['height']

    pygame.init()

    # Mapeo de códigos a cursores nativos
    CODE_TO_CURSOR = {
        0: pygame.SYSTEM_CURSOR_ARROW,
        1: pygame.SYSTEM_CURSOR_IBEAM,
        2: pygame.SYSTEM_CURSOR_HAND,
        3: pygame.SYSTEM_CURSOR_CROSSHAIR,
        4: pygame.SYSTEM_CURSOR_WAIT,
        5: pygame.SYSTEM_CURSOR_SIZENS,
        6: pygame.SYSTEM_CURSOR_SIZEWE,
        7: pygame.SYSTEM_CURSOR_SIZENWSE,
        8: pygame.SYSTEM_CURSOR_SIZENESW,
        9: pygame.SYSTEM_CURSOR_SIZEALL,
        10: pygame.SYSTEM_CURSOR_NO
    }

    local_info = pygame.display.Info()
    local_w, local_h = local_info.current_w, local_info.current_h

    if local_w >= native_w and local_h >= native_h:
        win_w, win_h = native_w, native_h
    else:
        scale_factor = min((local_w - 60) / native_w, (local_h - 80) / native_h, 1.0)
        win_w = int(native_w * scale_factor)
        win_h = int(native_h * scale_factor)

    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption(f"Control Remoto LAN - {server_ip} (F11: Pantalla Completa)")
    clock = pygame.time.Clock()

    fullscreen = False
    frame_lock = threading.Lock()
    latest_surface = None
    latest_cursor_code = 0
    active_cursor_code = -1
    running = True

    def send_event(ev_dict):
        try:
            msg = json.dumps(ev_dict) + '\n'
            input_sock.sendall(msg.encode('utf-8'))
        except Exception:
            pass

    def video_receiver_loop():
        nonlocal latest_surface, latest_cursor_code, running
        while running:
            try:
                hdr_bytes = recv_all(video_sock, 5)
                if not hdr_bytes:
                    break
                frame_size, cur_code = struct.unpack('>IB', hdr_bytes)
                frame_data = recv_all(video_sock, frame_size)
                if not frame_data:
                    break

                img_np = np.frombuffer(frame_data, dtype=np.uint8)
                frame_bgr = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                if frame_bgr is not None:
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    surf = pygame.image.frombuffer(frame_rgb.tobytes(), (native_w, native_h), 'RGB')
                    with frame_lock:
                        latest_surface = surf
                        latest_cursor_code = cur_code
            except Exception:
                break
        running = False

    t_recv = threading.Thread(target=video_receiver_loop, daemon=True)
    t_recv.start()

    last_mouse_send = 0

    while running:
        now = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    win_w, win_h = event.w, event.h
                    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        win_w, win_h = screen.get_size()
                    else:
                        win_w = min(local_w - 60, native_w)
                        win_h = int(win_w * (native_h / native_w))
                        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
                elif event.key == pygame.K_F10:
                    win_w, win_h = native_w, native_h
                    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
                else:
                    kname = pygame.key.name(event.key)
                    char = event.unicode if event.unicode else None
                    send_event({"type": "key_down", "key": kname, "char": char})

            elif event.type == pygame.KEYUP:
                kname = pygame.key.name(event.key)
                char = event.unicode if event.unicode else None
                send_event({"type": "key_up", "key": kname, "char": char})

            elif event.type == pygame.MOUSEMOTION:
                if now - last_mouse_send >= 0.010:
                    mx, my = event.pos
                    nx = max(0.0, min(1.0, mx / win_w))
                    ny = max(0.0, min(1.0, my / win_h))
                    send_event({"type": "mouse_move", "x": nx, "y": ny})
                    last_mouse_send = now

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 2, 3):
                    send_event({"type": "mouse_down", "button": event.button})
                elif event.button == 4:
                    send_event({"type": "mouse_scroll", "dy": 3})
                elif event.button == 5:
                    send_event({"type": "mouse_scroll", "dy": -3})

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 2, 3):
                    send_event({"type": "mouse_up", "button": event.button})

        # Actualizar cursor automáticamente
        with frame_lock:
            cur_code = latest_cursor_code
            surf_to_draw = latest_surface

        if cur_code != active_cursor_code:
            active_cursor_code = cur_code
            if cur_code in CODE_TO_CURSOR:
                try:
                    pygame.mouse.set_cursor(CODE_TO_CURSOR[cur_code])
                except Exception:
                    pass

        # Dibujar frame
        if surf_to_draw is not None:
            if win_w == native_w and win_h == native_h:
                screen.blit(surf_to_draw, (0, 0))
            else:
                scaled = pygame.transform.smoothscale(surf_to_draw, (win_w, win_h))
                screen.blit(scaled, (0, 0))
            pygame.display.flip()

        clock.tick(60)

    video_sock.close()
    input_sock.close()
    pygame.quit()
    print("Sesion terminada.")

if __name__ == '__main__':
    main()
