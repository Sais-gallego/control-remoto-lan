# Control Remoto Espejo LAN (Versión Profesional)

Sistema de control remoto directo **PC a PC por red local (LAN)** con transmisión de video, sonido de llamadas (Google Meet/Zoom), portapapeles compartido y transferencia de archivos.

---

### Nuevas Funciones Implementadas

1. **Portapapeles Compartido (Copiar y Pegar entre PCs):**  
   Copia cualquier texto, contraseña, enlace o mensaje en una PC con `Ctrl + C` y pégalo directamente en la otra con `Ctrl + V`. La sincronización es instantánea y bidireccional.
2. **Modo "Solo Observar" (Bloqueo de Ratón para el que controla):**  
   - Presiona **`F5`** en cualquier momento para activar o desactivar este modo.
   - **¿Para qué sirve?** Bloquea el envío de tus movimientos de ratón y clics hacia la otra PC. Puedes mover tu cursor libremente por la pantalla para ver y escuchar la llamada de Meet con total tranquilidad, sin riesgo de moverle el mouse a la otra persona por accidente.
   - Vuelve a presionar **`F5`** cuando quieras retomar el control activo.
3. **Transferencia Rápida de Archivos (Arrastrar y Soltar):**  
   Arrastra cualquier archivo desde tu explorador de Windows y **suéltalo directamente sobre la ventana de control remoto**. El archivo se transferirá a máxima velocidad por la red local y aparecerá automáticamente en el **Escritorio** de la otra PC.
4. **Funciones Especiales (Inicio Automático con Windows):**  
   Dentro de la carpeta `funciones_especiales/`:
   - **`ACTIVAR_INICIO_AUTOMATICO.bat`:** Hace que el servidor inicie en segundo plano automáticamente cada vez que se encienda esa computadora, para tener siempre acceso sin tocar nada.
   - **`DESACTIVAR_INICIO_AUTOMATICO.bat`:** Quita el inicio automático si ya no lo necesitas.
5. **Audio en Vivo (Google Meet, videos, llamadas):**  
   Escucha todo lo que suena en la otra computadora por tus altavoces o auriculares en tiempo real. Presiona **`M`** para silenciar/activar.

---

### Resumen de Atajos de Teclado (En la PC que controla)

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
