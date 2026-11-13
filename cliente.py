import socket
import struct
import json
import threading
import time
import sys
import os
import base64
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

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame

PORT_VIDEO = 5555
PORT_INPUT = 5556
PORT_DISCOVERY = 5557
PORT_AUDIO = 5558

def recv_all(sock, size):
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)

def auto_discover_server(timeout=1.2):
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

def audio_receiver_loop(server_ip, is_running_func, is_muted_func):
    if not HAS_AUDIO:
        return
    try:
        audio_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        audio_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        audio_sock.connect((server_ip, PORT_AUDIO))

        hdr_len_bytes = recv_all(audio_sock, 4)
        if not hdr_len_bytes:
            return
        hdr_len = struct.unpack('>I', hdr_len_bytes)[0]
        hdr_data = recv_all(audio_sock, hdr_len)
        info = json.loads(hdr_data.decode('utf-8'))

        rate = info.get('rate', 48000)
        channels = info.get('channels', 2)

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=rate,
            output=True,
            frames_per_buffer=1024
        )

        while is_running_func():
            sz_bytes = recv_all(audio_sock, 4)
            if not sz_bytes:
                break
            sz = struct.unpack('>I', sz_bytes)[0]
            audio_data = recv_all(audio_sock, sz)
            if not audio_data:
                break

            if not is_muted_func():
                stream.write(audio_data)

        stream.stop_stream()
        stream.close()
        p.terminate()
        audio_sock.close()
    except Exception:
        pass

def main():
    print("=" * 65)
    print("       CLIENTE DE CONTROL REMOTO LAN CON CHAT PRIVADO         ")
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

    hdr_len_bytes = recv_all(video_sock, 4)
    if not hdr_len_bytes:
        print("No se pudo recibir configuracion de pantalla.")
        return
    hdr_len = struct.unpack('>I', hdr_len_bytes)[0]
    hdr_data = recv_all(video_sock, hdr_len)
    info = json.loads(hdr_data.decode('utf-8'))
    native_w, native_h = info['width'], info['height']

    pygame.init()
    pygame.font.init()
    chat_font = pygame.font.SysFont("segoeui", 17)
    hint_font = pygame.font.SysFont("segoeui", 13)

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
    clock = pygame.time.Clock()

    fullscreen = False
    is_muted = False
    view_only_mode = False

    # Estado del chat privado
    is_chatting = False
    chat_input_text = ""

    status_notification = ""
    status_timer = 0
    running = True

    def update_window_title():
        if status_notification and time.time() < status_timer:
            pygame.display.set_caption(f"Control Remoto | {status_notification}")
            return

        mode_str = "[MODO: SOLO OBSERVAR]" if view_only_mode else "[CONTROL ACTIVO]"
        audio_str = "MUTED" if is_muted else "AUDIO ON"
        pygame.display.set_caption(
            f"Control Remoto LAN - {server_ip} | {mode_str} | {audio_str} | F9: Chat Privado (Meet) | F5: Bloquear | M: Silenciar"
        )

    update_window_title()

    frame_lock = threading.Lock()
    latest_surface = None
    latest_cursor_code = 0
    active_cursor_code = -1
    last_clipboard = ""

    def send_event(ev_dict):
        try:
            msg = json.dumps(ev_dict) + '\n'
            input_sock.sendall(msg.encode('utf-8'))
        except Exception:
            pass

    def send_file(filepath):
        nonlocal status_notification, status_timer
        try:
            fname = os.path.basename(filepath)
            fsize = os.path.getsize(filepath)
            status_notification = f"Enviando '{fname}' ({round(fsize / (1024*1024), 1)} MB)..."
            status_timer = time.time() + 5
            update_window_title()

            send_event({"type": "file_start", "filename": fname, "filesize": fsize})

            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    b64_chunk = base64.b64encode(chunk).decode('ascii')
                    send_event({"type": "file_chunk", "data": b64_chunk})

            send_event({"type": "file_end", "filename": fname})

            status_notification = f"¡'{fname}' enviado al Escritorio de la otra PC!"
            status_timer = time.time() + 4
            update_window_title()
        except Exception as e:
            status_notification = f"Error al enviar archivo: {e}"
            status_timer = time.time() + 4
            update_window_title()

    def input_receiver_loop():
        nonlocal last_clipboard, running
        buffer = ""
        while running:
            try:
                data = input_sock.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8', errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if event.get('type') == 'clipboard':
                        text = event.get('text', '')
                        if HAS_CLIPBOARD and text:
                            last_clipboard = text
                            pyperclip.copy(text)
            except Exception:
                break

    t_in_recv = threading.Thread(target=input_receiver_loop, daemon=True)
    t_in_recv.start()

    def clipboard_monitor():
        nonlocal last_clipboard, running
        if not HAS_CLIPBOARD:
            return
        while running:
            try:
                text = pyperclip.paste()
                if text and text != last_clipboard:
                    last_clipboard = text
                    send_event({"type": "clipboard", "text": text})
            except Exception:
                pass
            time.sleep(0.4)

    t_clip = threading.Thread(target=clipboard_monitor, daemon=True)
    t_clip.start()

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

    t_audio = threading.Thread(
        target=audio_receiver_loop,
        args=(server_ip, lambda: running, lambda: is_muted),
        daemon=True
    )
    t_audio.start()

    last_mouse_send = 0

    while running:
        now = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.DROPFILE:
                dropped_path = event.file
                if os.path.isfile(dropped_path):
                    threading.Thread(target=send_file, args=(dropped_path,), daemon=True).start()

            elif event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    win_w, win_h = event.w, event.h
                    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                # Si estamos escribiendo un mensaje privado, las teclas van al chat y NO a la PC remota
                if is_chatting:
                    if event.key == pygame.K_RETURN:
                        if chat_input_text.strip():
                            send_event({"type": "private_chat", "text": chat_input_text.strip()})
                            status_notification = "¡Mensaje privado enviado (Invisible en Meet)!"
                            status_timer = now + 4
                            update_window_title()
                        is_chatting = False
                        chat_input_text = ""
                    elif event.key == pygame.K_ESCAPE:
                        is_chatting = False
                        chat_input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input_text = chat_input_text[:-1]
                    else:
                        if event.unicode and len(chat_input_text) < 120:
                            chat_input_text += event.unicode
                    continue

                # Atajos generales
                if event.key == pygame.K_F9:
                    # Abrir barra de chat privado
                    is_chatting = True
                    chat_input_text = ""
                elif event.key == pygame.K_F5:
                    view_only_mode = not view_only_mode
                    update_window_title()
                elif event.key == pygame.K_m:
                    is_muted = not is_muted
                    update_window_title()
                elif event.key == pygame.K_F11:
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
                elif not view_only_mode:
                    if event.key == pygame.K_F1:
                        send_event({"type": "special_action", "action": "win_key"})
                    elif event.key == pygame.K_F2:
                        send_event({"type": "special_action", "action": "alt_tab"})
                    elif event.key == pygame.K_F3:
                        send_event({"type": "special_action", "action": "win_tab"})
                    elif event.key == pygame.K_F4:
                        send_event({"type": "special_action", "action": "show_desktop"})
                    else:
                        kname = pygame.key.name(event.key)
                        char = event.unicode if event.unicode else None
                        send_event({"type": "key_down", "key": kname, "char": char})

            elif event.type == pygame.KEYUP:
                if not is_chatting and not view_only_mode:
                    if event.key not in (pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4, pygame.K_F5, pygame.K_F9, pygame.K_F10, pygame.K_F11, pygame.K_m):
                        kname = pygame.key.name(event.key)
                        char = event.unicode if event.unicode else None
                        send_event({"type": "key_up", "key": kname, "char": char})

            elif event.type == pygame.MOUSEMOTION:
                if not view_only_mode:
                    if now - last_mouse_send >= 0.010:
                        mx, my = event.pos
                        nx = max(0.0, min(1.0, mx / win_w))
                        ny = max(0.0, min(1.0, my / win_h))
                        send_event({"type": "mouse_move", "x": nx, "y": ny})
                        last_mouse_send = now

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not view_only_mode:
                    if event.button in (1, 2, 3):
                        send_event({"type": "mouse_down", "button": event.button})
                    elif event.button == 4:
                        send_event({"type": "mouse_scroll", "dy": 3})
                    elif event.button == 5:
                        send_event({"type": "mouse_scroll", "dy": -3})

            elif event.type == pygame.MOUSEBUTTONUP:
                if not view_only_mode:
                    if event.button in (1, 2, 3):
                        send_event({"type": "mouse_up", "button": event.button})

        if status_notification and now >= status_timer:
            status_notification = ""
            update_window_title()

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

        # Dibujar pantalla remota
        if surf_to_draw is not None:
            if win_w == native_w and win_h == native_h:
                screen.blit(surf_to_draw, (0, 0))
            else:
                scaled = pygame.transform.smoothscale(surf_to_draw, (win_w, win_h))
                screen.blit(scaled, (0, 0))

        # Dibujar barra de Chat Privado si esta activa
        if is_chatting:
            bar_h = 48
            bar_y = win_h - bar_h
            # Fondo oscuro elegante
            bar_surface = pygame.Surface((win_w, bar_h), pygame.SRCALPHA)
            bar_surface.fill((24, 24, 37, 240))
            screen.blit(bar_surface, (0, bar_y))
            pygame.draw.line(screen, (137, 180, 250), (0, bar_y), (win_w, bar_y), 2)

            prefix = "💬 Mensaje Privado (Oculto en Meet): "
            prefix_surf = chat_font.render(prefix, True, (137, 180, 250))
            screen.blit(prefix_surf, (15, bar_y + 12))

            cursor_char = "|" if int(now * 2) % 2 == 0 else ""
            txt_surf = chat_font.render(chat_input_text + cursor_char, True, (255, 255, 255))
            screen.blit(txt_surf, (15 + prefix_surf.get_width(), bar_y + 12))

            hint_text = "[Enter: Enviar | Esc: Cancelar]"
            hint_surf = hint_font.render(hint_text, True, (166, 173, 200))
            screen.blit(hint_surf, (win_w - hint_surf.get_width() - 15, bar_y + 16))

        pygame.display.flip()
        clock.tick(60)

    video_sock.close()
    input_sock.close()
    pygame.quit()
    print("Sesion terminada.")

if __name__ == '__main__':
    main()
