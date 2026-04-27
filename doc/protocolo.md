## Protocolo de Aplicación — RFTP (Reliable File Transfer Protocol)

### Principio de diseño

El protocolo tiene **dos capas bien separadas**:

- **Capa RDT** — garantiza entrega confiable de segmentos individuales (S&W o SR)
- **Capa de Aplicación** — define qué operaciones existen (UPLOAD/DOWNLOAD) y cómo se intercambian los mensajes

La capa de aplicación **no sabe nada** de ACKs, retransmisiones ni números de secuencia. Solo ve mensajes completos entregados por la capa RDT.

---

### Tipos de mensaje

```
TYPE byte:
  0x01 = REQUEST   → el cliente pide una operación
  0x02 = RESPONSE  → el servidor responde
  0x03 = DATA      → chunk de datos del archivo
  0x04 = ERR       → error de cualquiera de los dos lados
```

---

### Formatos de mensaje

**REQUEST UPLOAD**
```
[TYPE=0x01][OP=UPLOAD][PROTOCOL][FILESIZE(4)][FILENAME_LEN(1)][FILENAME(N)]
```

**REQUEST DOWNLOAD**
```
[TYPE=0x01][OP=DOWNLOAD][PROTOCOL][FILENAME_LEN(1)][FILENAME(N)]
```
- `PROTOCOL` indica a qué protocolo RDT cambiar: Stop&Wait o Selective Repeat

**RESPONSE OK**
```
[TYPE=0x02][STATE=OK]
```

**RESPONSE con filesize** (solo en download)
```
[TYPE=0x02][STATE=OK][FILESIZE(4)]
```

**DATA chunk**
```
[TYPE=0x03][MORE(1)][PAYLOAD(N)]
```
- `MORE=0x01` → hay más chunks
- `MORE=0x00` → último chunk
- Payload máximo: **32 KB por chunk**

**ERR**
```
[TYPE=0x04][CODE(1)]
```

| Código | Significado |
|---|---|
| `FILE_NOT_FOUND` | El archivo no existe en el servidor |
| `INVALID_FILENAME` | Nombre vacío, con `/`, `\` o `..` |
| `FILESIZE_MISMATCH` | Tamaño recibido ≠ tamaño declarado |
| `WRITE_ERROR` | Error al escribir en disco |
| `USER_CANCELLED` | El cliente canceló la transferencia |

---

### Flujo UPLOAD

```
Cliente                              Servidor
  |                                     |
  |--[REQUEST UPLOAD, filename, size]-->|
  |                                     | valida nombre
  |<----------[RESPONSE OK]-------------|
  |                                     |
  |--[DATA, chunk1, MORE=1]------------>|
  |--[DATA, chunk2, MORE=1]------------>|
  |--[DATA, chunkN, MORE=0]------------>| ← último
  |                                     | escribe archivo
  |<----------[RESPONSE OK]-------------|
```

**Flujo de error — nombre inválido:**
```
  |--[REQUEST UPLOAD, "../malo.txt"]-->|
  |<--------[ERR, INVALID_FILENAME]----|
```

---

### Flujo DOWNLOAD

```
Cliente                              Servidor
  |                                     |
  |--[REQUEST DOWNLOAD, filename]------>|
  |                                     | busca archivo
  |<-----[RESPONSE OK, filesize]--------|
  |                                     |
  |--[RESPONSE OK]--------------------->| ← confirmación
  |                                     |
  |<----[DATA, chunk1, MORE=1]----------|
  |<----[DATA, chunk2, MORE=1]----------|
  |<----[DATA, chunkN, MORE=0]----------| ← último
```

**Flujo de error — archivo inexistente:**
```
  |--[REQUEST DOWNLOAD, "noexiste"]---->|
  |<--------[ERR, FILE_NOT_FOUND]-------|
```

---

### Fragmentación

Los archivos se dividen en chunks de **32 KB** en la capa de aplicación. Cada chunk es un mensaje `DATA` independiente que la capa RDT entrega de forma confiable. El campo `MORE` indica si hay más chunks por venir. El receptor los reensambla en orden antes de escribir el archivo.

Esto permite transferir archivos de cualquier tamaño sin importar el límite de 65507 bytes del datagrama UDP.

---

### Negociación de protocolo RDT

El cliente incluye en el `REQUEST` qué protocolo RDT quiere usar. El servidor cambia su instancia RDT antes de procesar la transferencia. Esto permite que distintos clientes usen S&W o SR simultáneamente en el mismo servidor.

---

### Concurrencia

El servidor crea un hilo por cliente. Cada hilo tiene su propia cola (`Queue`) de segmentos entrantes — el `Dispatcher` lee del socket compartido y enruta cada segmento a la cola del cliente correspondiente según la dirección IP y puerto de origen.
