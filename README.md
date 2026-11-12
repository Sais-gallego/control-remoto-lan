# Control Remoto Espejo LAN (PC a PC Directo)

Un sistema de control remoto de baja latencia diseñado para **comunicación 100% directa entre dos PCs en la misma red local (Wi-Fi o cable Ethernet)**.

### Características
- **Sin intermediarios (Sin servidores en la nube):** La conexión es directa PC ↔ PC por sockets TCP locales.
- **Sin marco amarillo:** No utiliza la API de captura intrusiva de Windows.
- **Efecto Espejo (Colaboración en tiempo real):** La persona frente a la PC destino ve exactamente lo que haces (movimiento del cursor, ventanas abriéndose, clics y teclado).
- **Control fluido:** Soporta movimiento de ratón, clics (izquierdo, derecho, rueda), scroll y teclado.
- **Pantalla completa:** Presiona **`F11`** en la ventana del cliente para alternar pantalla completa.

---

### Instrucciones de Uso

#### En la PC que quieres MANIPULAR (PC Destino):
1. Copia la carpeta `control_remoto_lan` a esa computadora (por memoria USB o compartiendo carpeta).
2. Haz doble clic en **`INICIAR_SERVIDOR.bat`** (o ejecuta `python servidor.py`).
3. La consola te mostrará en pantalla su IP local (por ejemplo: `192.168.1.50`).

#### En tu PC (la que va a CONTROLAR):
1. Haz doble clic en **`INICIAR_CLIENTE.bat`** (o ejecuta `python cliente.py`).
2. Escribe la dirección IP que te mostró la otra PC y presiona **Enter**.
3. ¡Listo! Se abrirá una ventana con la pantalla de la otra computadora y podrás mover el ratón, hacer clics y abrir cualquier programa.

---

### Notas y Solución de Problemas
- **Firewall de Windows:** La primera vez que abras el servidor, Windows te preguntará si deseas permitir el acceso a través del Firewall. Asegúrate de marcar **"Redes privadas"** y pulsar **Permitir acceso**.
- **Ambas PCs deben estar en la misma red:** Conectadas al mismo router (ya sea por cable o por la misma señal Wi-Fi).
