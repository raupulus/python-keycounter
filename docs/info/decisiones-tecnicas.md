# Decisiones técnicas

Decisiones deliberadas que alguien podría querer «corregir» sin conocer el
motivo. No es una lista de bugs ni de deuda técnica.

## D1 — SQLite local como caché, no como almacén definitivo
La base de datos `keycounter.db` es una **caché temporal**: [main](main.md) sube
las rachas a la API y luego borra los registros locales
(`table_drop_last_elements`). Por eso `keycounter.db` está en `.gitignore` y no se
espera que crezca indefinidamente.

## D2 — Comunicación con otros procesos vía UNIX socket
Se expone la estadística en tiempo real por un UNIX socket
(`/var/run/keycounter.socket`) en lugar de un puerto TCP para integrarlo con
barras de estado locales (i3pystatus, la app de macOS) sin abrir red. Implica
ejecutar como root.

## D3 — Rachas (spurts) agrupadas por ventana de inactividad
Las pulsaciones se agrupan en «rachas» separadas por `COMBO_RESET = 15 s` de
inactividad. Es el criterio de negocio para medir intensidad de tecleo, no un
detalle de implementación.

## D4 — Captura de teclado apoyada en internos de la librería `keyboard`
[keylogger](keylogger.md) accede a atributos privados (`keyboard._nixkeyboard`,
`keyboard._KeyboardListener`) para reconstruir el listener al conectar/desconectar
dispositivos. Es frágil ante cambios de la librería pero era la forma de soportar
teclados USB conectados en caliente en Linux.

## D5 — Ejecución multihilo con `_thread.start_new_thread`
Se usa `start_new_thread` para captura, socket, pantalla y cliente en red. Es
deliberadamente simple; no hay gestión de ciclo de vida ni pools.

## D6 — «WebSocket» que en realidad es TCP plano
[client-display-websocket](client-display-websocket.md) se llama así por historia
pero usa un socket TCP plano contra el puerto 80 del dispositivo en red. No es el
protocolo WebSocket.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
