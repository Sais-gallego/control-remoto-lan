# Control Remoto Espejo LAN (Versión Profesional)

Sistema de control remoto directo **PC a PC por red local (LAN)** con transmisión de video, sonido de llamadas (Google Meet/Zoom), portapapeles compartido, transferencia de archivos y **chat privado invisible para transmisiones de pantalla**.

---

### Nuevas Funciones Implementadas

1. **Chat Privado Discreto (Invisible en Google Meet / Zoom):**  
   - Presiona **`F9`** en la ventana de control remoto para abrir la barra de chat privada.
   - Escribe tu indicación (ej. *"Abre el micrófono"*, *"Pasa a la siguiente lámina"*, *"Ya te pasé el archivo"*) y presiona **Enter**.
   - **Exclusión de captura de pantalla (`WDA_EXCLUDEFROMCAPTURE`):** En la otra PC aparece una tarjeta flotante elegante con el mensaje, pero **Google Meet, Zoom, Teams o grabadores de pantalla NO LA MUESTRAN**. Para los demás participantes de la llamada de Meet, la pantalla se ve completamente limpia: nadie sabrá que le estás enviando mensajes privados.
   - Al escribir en el chat con `F9`, tus teclas no se escribirán por error en las ventanas de la otra PC.
2. **Portapapeles Compartido (Copiar y Pegar entre PCs):**  
   Copia cualquier texto o enlace en una PC con `Ctrl + C` y pégalo directamente en la otra con `Ctrl + V`.
3. **Modo "Solo Observar" (Bloqueo de Ratón para el que controla):**  
   - Presiona **`F5`** para activar o desactivar el envío de tus movimientos de ratón. Te permite ver y escuchar la llamada de Meet sin riesgo de mover el cursor ajeno.
4. **Transferencia Rápida de Archivos (Arrastrar y Soltar):**  
   Arrastra cualquier archivo desde tu explorador de Windows y **suéltalo dentro de la ventana**. El archivo se transferirá a máxima velocidad y aparecerá en el **Escritorio** de la otra PC.
5. **Audio en Vivo (Meet, videos, llamadas):**  
   Escucha todo lo que suena en la otra computadora por tus altavoces o auriculares en tiempo real. Presiona **`M`** para silenciar/activar.
6. **Inicio Automático con Windows (Opcional):**  
   En la carpeta `funciones_especiales/`:
   - `ACTIVAR_INICIO_AUTOMATICO.bat` para iniciar en segundo plano cada vez que se encienda la PC.
   - `DESACTIVAR_INICIO_AUTOMATICO.bat` para quitarlo.

---

### Resumen de Atajos de Teclado (En la PC que controla)

- **`F9`:** Abrir / Cerrar **Chat Privado (Invisible en Meet)**.
- **`F5`:** Alternar Modo **Solo Observar** (Bloquear/Desbloquear ratón para el que controla).
- **`M`:** Silenciar / Activar audio remoto.
- **`Arrastrar archivo a la ventana`:** Envía el archivo al Escritorio de la otra PC.
- **`F1`:** Abrir menú de Inicio remoto (tecla Windows).
- **`F2`:** Selector de ventanas (**Alt + Tab** remoto).
- **`F3`:** Vista de tareas (**Win + Tab**).
- **`F4`:** Mostrar escritorio (**Win + D**).
- **`F11`:** Pantalla completa.
- **`F10`:** Tamaño 1:1 original.

---

### Instrucciones de Uso

#### En la PC a manipular (Servidor):
- Ejecuta **`INICIAR_SERVIDOR.bat`** (corre invisible en segundo plano).
- Para detenerlo cuando termines, ejecuta **`DETENER_SERVIDOR.bat`**.

#### En tu PC (Cliente):
- Ejecuta **`INICIAR_CLIENTE.bat`**; detectará la otra PC en la red y presiona **Enter** para entrar.
