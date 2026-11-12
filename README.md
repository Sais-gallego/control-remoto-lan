# Control Remoto Espejo LAN (Alto Rendimiento)

Sistema de control remoto optimizado para **red local LAN (Wi-Fi o cable Ethernet)** con respuesta inmediata, cero servidores en la nube y máxima fidelidad de imagen.

---

### Principales Optimizaciones de Rendimiento
1. **Detección Dinámica de Cambios (Strided Frame Diff):**  
   Solo comprime y envía datos cuando la pantalla cambia o el cursor se mueve. Si estás leyendo o la pantalla está estática, reduce el consumo de red y procesador a casi 0%.
2. **Hilo de Red Desacoplado (Asíncrono):**  
   La recepción de video y los eventos del teclado/ratón corren en hilos independientes, eliminando congelamientos o retrasos acumulados (*buffer bloat*).
3. **Control de Ratón a 100 Hz:**  
   Frecuencia de respuesta instantánea sin saturar los paquetes TCP.
4. **Instancia Persistente de Captura:**  
   Ahorra entre 10 y 15 ms por cada fotograma.

---

### Controles y Atajos en Vivo (En la PC Controladora)

Puedes cambiar la calidad al vuelo presionando las teclas de tu teclado:
- **`Tecla 1` (Modo Rápido):** Calidad optimizada para menor consumo o si el Wi-Fi tiene poca señal.
- **`Tecla 2` (Modo Equilibrado - Por defecto):** Excelente calidad (85%) y máxima fluidez. Muy recomendado.
- **`Tecla 3` (Modo Ultra HD):** Máxima fidelidad de imagen (92% Chroma 4:4:4) para texto ultra nítido.
- **`F11`:** Alternar pantalla completa.
- **`F10`:** Forzar tamaño de pantalla nativo 1:1.

---

### Instrucciones de Uso

1. **En la PC a MANIPULAR (Servidor):**
   - Ejecuta `INICIAR_SERVIDOR.bat`.
   - Te mostrará la dirección IP local en pantalla.

2. **En tu PC (Cliente):**
   - Ejecuta `INICIAR_CLIENTE.bat`.
   - Escribe la IP de la otra PC y presiona Enter.
