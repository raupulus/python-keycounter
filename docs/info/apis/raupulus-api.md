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
| Info del dispositivo pantalla | `GET` | `/hardware/devices/{DISPLAY_ID}?include=status` | `ApiConnection.get_websocket_server_display_info` (id `DISPLAY_ID`, token `DISPLAY_API_TOKEN`) |

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

## Respuesta de la info de dispositivo (verificada)
`GET /hardware/devices/{id}?include=status` responde con el envelope v2
`{ "success": true, "message": ..., "data": { ...dispositivo... } }`. Se consulta
el dispositivo pantalla (`DISPLAY_ID`) con su propio token (`DISPLAY_API_TOKEN`),
porque el token de keycounter no puede leer otros dispositivos. Verificado con
petición real (device 16 = Raspberry Pi Pico Display, `200`): `data` trae datos
estáticos (`id`, `user_id`, `name`, `type`, `brand`, `model`, versiones...) **y**,
gracias a `include=status`, un objeto anidado `data.status` con el estado
dinámico:

```json
"status": {
  "hardware_device_id": 16,
  "temp": null, "voltage": null, "battery_level": null,
  "cpu": null, "disk": null, "ram": null, "uptime": null,
  "ip_local": "172.18.1.209",
  "ip_public": "139.47.158.109",
  "extra": null,
  "last_seen_at": "2026-09-05T10:59:24.000000Z"
}
```

`ip_local` vive ahí, no en `data` directamente. Sin `include=status` la API omite
este bloque por completo.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
