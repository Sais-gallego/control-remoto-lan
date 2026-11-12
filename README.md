# Control Remoto Espejo LAN

Sistema de control remoto directo **PC a PC por red local (LAN)**, diseñado para ser rápido, discreto y sin complicaciones.

---

### Novedades y Características

1. **Sin terminal en la barra de tareas (PC a manipular):**  
   Al iniciar el servidor, se ejecuta completamente en segundo plano mediante `pythonw.exe`. No deja ninguna ventana negra de consola ni icono en la barra de tareas.
2. **Modo Único Equilibrado:**  
   Se eliminó la selección de múltiples modos. El sistema opera en un único perfil optimizado que combina alta velocidad a 60 FPS con nitidez de texto sin sobrecargar el procesador ni la red.
3. **Detección Automática de IP:**  
   Al abrir el cliente, buscará la PC en la red local automáticamente; solo presionas **Enter** para conectarte sin tener que escribir los números a mano.
4. **Sincronización Dinámica de Cursores:**  
   El ratón cambia automáticamente a la barra de texto (**I-Beam**) en cuadros de entrada, a la mano (**Hand**) en enlaces y a las flechas de redimensionar (**Resize**) en los bordes.

---

### Instrucciones de Uso

#### En la PC a manipular (Servidor):
- Haz doble clic en **`INICIAR_SERVIDOR.bat`**.  
  *(Aparecerá un aviso breve con la IP para tu información y luego se ejecutará silenciosamente en segundo plano, sin estorbar en la barra de tareas).*
- Para detener el servicio cuando termines, haz doble clic en **`DETENER_SERVIDOR.bat`**.

#### En tu PC (Cliente):
- Haz doble clic en **`INICIAR_CLIENTE.bat`**.  
- Detectará la otra computadora en la red; presiona **Enter** para conectar.
- Presiona **`F11`** para activar/desactivar la pantalla completa.
