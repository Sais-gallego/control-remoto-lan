import socket
import struct
import json
import threading
import sys
import os
import cv2
import numpy as np

# Desactivar mensaje de bienvenida de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame

PORT_VIDEO = 5555
PORT_INPUT = 5556

def recv_all(sock, size):
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)

def main():
    print("=" * 60)
    print("       CLIENTE DE CONTROL REMOTO LAN (PC CONTROLADORA)        ")
    print("=" * 60)

    if len(sys.argv) > 1:
        server_ip = sys.argv[1].strip()
    else:
        server_ip = input("Ingresa la direccion IP de la PC a manipular: ").strip()

    if not server_ip:
        print("Direccion IP invalida.")
        return

    print(f"\nConectando a {server_ip}...")

    try:
        video_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        video_sock.connect((server_ip, PORT_VIDEO))
        video_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        input_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        input_sock.connect((server_ip, PORT_INPUT))
        input_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
    # Iniciar ventana con tamaño proporcional (ej. 80% de la pantalla o 1280x720 base)
    win_w = min(1366, int(native_w * 0.85))
    win_h = int(win_w * (native_h / native_w))

    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption(f"Control Remoto LAN - Conectado a {server_ip} (F11: Pantalla Completa)")
    clock = pygame.time.Clock()

    fullscreen = False

    def send_event(ev_dict):
        try:
            msg = json.dumps(ev_dict) + '\n'
            input_sock.sendall(msg.encode('utf-8'))
        except Exception:
            pass

    running = True

    while running:
        # 1. Procesar eventos de pygame (mouse y teclado)
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
                        win_w = min(1366, int(native_w * 0.85))
                        win_h = int(win_w * (native_h / native_w))
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
                mx, my = event.pos
                nx = max(0.0, min(1.0, mx / win_w))
                ny = max(0.0, min(1.0, my / win_h))
                send_event({"type": "mouse_move", "x": nx, "y": ny})

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 2, 3):
                    send_event({"type": "mouse_down", "button": event.button})
                elif event.button == 4:  # Rueda arriba
                    send_event({"type": "mouse_scroll", "dy": 3})
                elif event.button == 5:  # Rueda abajo
                    send_event({"type": "mouse_scroll", "dy": -3})

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 2, 3):
                    send_event({"type": "mouse_up", "button": event.button})

        # 2. Recibir frame de video
        size_bytes = recv_all(video_sock, 4)
        if not size_bytes:
            print("El servidor cerro la conexion.")
            break
        frame_size = struct.unpack('>I', size_bytes)[0]
        frame_data = recv_all(video_sock, frame_size)
        if not frame_data:
            break

        # Decodificar JPEG
        img_np = np.frombuffer(frame_data, dtype=np.uint8)
        frame_bgr = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        if frame_bgr is not None:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            img_surf = pygame.image.frombuffer(frame_rgb.tobytes(), (native_w, native_h), 'RGB')
            scaled_surf = pygame.transform.scale(img_surf, (win_w, win_h))
            screen.blit(scaled_surf, (0, 0))
            pygame.display.flip()

        clock.tick(60)

    video_sock.close()
    input_sock.close()
    pygame.quit()
    print("Sesion terminada.")

if __name__ == '__main__':
    main()
