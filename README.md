# Control Remoto Espejo LAN

Sistema de control remoto directo **PC a PC por red local (LAN)**, diseñado para una experiencia 100% idéntica a estar frente a la computadora real.

---

### Nuevas Mejoras de Control de Ventanas

1. **Vistas previas de la barra de tareas (Hover / Miniaturas de ventanas):**  
   Al pasar el ratón por los iconos de las aplicaciones abiertas en la barra de tareas o menús, ahora se activan los eventos nativos de Windows (`mouse_event` con DWM) para que **se desplieguen las miniaturas y ventanas flotantes** tal como en una computadora normal.
2. **Captura completa de ventanas translúcidas (*Layered Windows*):**  
   Garantiza que todos los menús desplegables, efectos Aero/Acrílico de Windows 10/11 y ventanas de previsualización se transmitan con total nitidez.
3. **Atajos para manipular ventanas en la PC remota:**
   - **`F1`:** Tecla Windows (Abre/Cierra el Menú de Inicio remoto).
   - **`F2`:** **Alt + Tab** remoto (Muestra el selector de ventanas abiertas para cambiar entre ellas).
   - **`F3`:** **Win + Tab** (Vista de tareas: muestra todas las ventanas abiertas en grande).
   - **`F4`:** **Win + D** (Minimizar todo y mostrar escritorio remoto / restaurar).
   - **`F11`:** Pantalla completa.
   - **`F10`:** Forzar tamaño nativo 1:1.

---

### Instrucciones de Uso

#### En la PC a manipular (Servidor):
- Haz doble clic en **`INICIAR_SERVIDOR.bat`**.  
  *(Se ejecuta en segundo plano, sin estorbar en la barra de tareas).*
- Para detener el servicio cuando termines, haz doble clic en **`DETENER_SERVIDOR.bat`**.

#### En tu PC (Cliente):
- Haz doble clic en **`INICIAR_CLIENTE.bat`**.  
- Detectará la otra computadora en la red; presiona **Enter** para conectar.
