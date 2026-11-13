# Control Remoto Espejo LAN (Con Audio en Vivo)

Sistema de control remoto directo **PC a PC por red local (LAN)** con transmisión de **video, ratón, teclado y audio en tiempo real**.

---

### Nuevas Características y Audio en Tiempo Real

1. **Transmisión de Audio en Vivo (Google Meet, videos, llamadas):**  
   Todo lo que se escuche en la PC remota (las voces de una reunión de Meet/Zoom, videos de YouTube, Spotify o sonidos del sistema) se captura directamente desde el dispositivo de audio del sistema (WASAPI Loopback) y se reproduce en los altavoces o auriculares de la PC que controla.
2. **Control de silencio con una tecla:**  
   Presiona la tecla **`M`** en la ventana del cliente para silenciar o reactivar el audio remoto en cualquier momento.
3. **Vistas previas de ventanas y miniaturas:**  
   Al pasar el ratón por los iconos de la barra de tareas se muestran las ventanas flotantes en miniatura.
4. **Atajos para manipular ventanas en la PC remota:**
   - **`M`:** Silenciar / Activar audio remoto.
   - **`F1`:** Tecla Windows (Menú Inicio remoto).
   - **`F2`:** **Alt + Tab** remoto (Selector de ventanas).
   - **`F3`:** **Win + Tab** (Vista de tareas).
   - **`F4`:** **Win + D** (Mostrar escritorio remoto).
   - **`F11`:** Pantalla completa.
   - **`F10`:** Tamaño nativo 1:1.

---

### Instrucciones de Uso

#### En la PC a manipular (Servidor):
- Haz doble clic en **`INICIAR_SERVIDOR.bat`**.  
  *(Se ejecuta en segundo plano con audio activado, sin estorbar en la barra de tareas).*
- Para detener el servicio cuando termines, haz doble clic en **`DETENER_SERVIDOR.bat`**.

#### En tu PC (Cliente):
- Haz doble clic en **`INICIAR_CLIENTE.bat`**.  
- Detectará la otra computadora en la red; presiona **Enter** para conectar y comenzarás a ver la pantalla y escuchar el sonido en vivo.
