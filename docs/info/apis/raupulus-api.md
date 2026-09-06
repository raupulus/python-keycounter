# Integración con la API de raupulus.dev

Cómo **integramos nosotros** esta API desde el proyecto. No duplica la
especificación oficial de la API (que, cuando se destile y verifique con
peticiones reales, debe vivir en `docs/apis/raupulus/`).

> ⚠️ **Sin verificar contra peticiones reales.** Todo lo de este documento está
> extraído del código del cliente ([api-connection](../api-connection.md)),
> **no** de una respuesta real de la API. Según la regla 11 del protocolo, no se
> debe configurar nada a partir de esto sin comprobarlo con una petición real.

## Base y autenticación
- Base configurable por `API_URL` (`.env.example`: `http://example.com`,
  producción: `https://api.raupulus.dev/api/v2`).
- Autenticación por cabecera `Authorization: Bearer <API_TOKEN>`.
- `Content-type: application/json`, `Accept: application/json`, timeout 30 s,
  3 reintentos en `500/502/504`.

## Endpoints que consumimos
| Uso | Método | Ruta (relativa a `API_URL`) | Origen |
|-----|--------|-----------------------------|--------|
| Subir rachas de teclado | `POST` | `/keycounter/keyboard-sessions` | `KeyboardLogger.api_path` |
| Subir rachas de ratón | `POST` | `/keycounter/mouse-sessions` | `MouseLogger.api_path` |
| Info del dispositivo pantalla en red | `GET` | `/hardware/v1/get/device/16/info` | `ApiConnection.get_websocket_server_display_info` (id **16** hardcodeado) |

> Nota: aunque `ApiConnection.send` recibe un parámetro `method`, siempre realiza
> `POST` (ver [api-connection](../api-connection.md), trampas conocidas).

## Códigos de respuesta que tratamos
- `201` → guardado correcto (`True`).
- `200` → guardado con errores parciales, se considera éxito (`True`).
- Otro → fallo (`False`).

## Cuerpo enviado (subida de rachas)
JSON de un registro por petición, con los campos del `tablemodel()` del modelo
correspondiente (ver [keyboard-logger](../keyboard-logger.md) y
[mouse-logger](../mouse-logger.md)), omitiendo la columna `id`.

## Respuesta esperada de la info de dispositivo
Se espera un objeto con clave `device` que contenga, entre otros, `ip_local`
(usado por [client-display-websocket](../client-display-websocket.md)). Estructura
**sin verificar**.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
