# FRDT — File Reliable Data Transfer

Implementación de un protocolo de transferencia de archivos confiable sobre UDP, con soporte para **Stop and Wait** y **Selective Repeat**. Desarrollado en el contexto de Redes de Computadoras.

## Integrantes

- 
- 
- Quispe Brian Gabriel - 109565

---

## Quickstart

### 0. Preparar el entorno

```bash
cd src
chmod +x start-server upload download
```

### 1. Generar archivos de prueba

Antes de abrir Mininet, crear archivos binarios de distintos tamaños para probar la transferencia:

```bash
# 100 KB
dd if=/dev/urandom of=test_100kb.bin bs=1K count=100

# 1 MB
dd if=/dev/urandom of=test_1mb.bin bs=1M count=1

# 10 MB
dd if=/dev/urandom of=test_10mb.bin bs=1M count=10

# 50 MB  (para estresar el protocolo)
dd if=/dev/urandom of=test_50mb.bin bs=1M count=50
```

### 2. Levantar Mininet

Sal de `src` y ejecuta el script asi:

```bash
cd ..
./lib/ejecutar_mn.sh
```

Esto simplemente hace (dentro de `src`):

```bash
cd src
sudo mn --custom ./lib/topologia.py --topo tp2 --mac --switch ovsk --controller none -x
```

Esto abre **3 terminales**: una por cada nodo (`h1`, `h2`) y una del switch. Usar las de `h1` y `h2`.

### 3. En la terminal de h2 → Servidor

```bash
python3 start-server -H 10.0.0.2 -p 65535 -s ./storage -v
```

### 4. En la terminal de h1 → Cliente

**Upload** (Stop & Wait):
```bash
python3 upload -s test_1mb.bin -n test_1mb.bin -H 10.0.0.2 -r 1 -v
```

**Upload** (Selective Repeat):
```bash
python3 upload -s test_10mb.bin -n test_10mb.bin -H 10.0.0.2 -r 2 -v
```

**Download**:
```bash
python3 download -d ./descargas -n test_1mb.bin -H 10.0.0.2 -r 2 -v
```

### 5. Verificar integridad del archivo transferido

```bash
# Comparar el archivo original con el recibido en el servidor
md5sum test_1mb.bin storage/test_1mb.bin
# Los dos hashes deben ser idénticos
```

---

## Plugin de Wireshark

Se incluye un disector Lua (`rdt2_redes.lua`) que permite inspeccionar el tráfico FRDT en Wireshark con campos decodificados (opcode, seq, window size, checksum, payload).

### Instalación

```bash
sudo bash src/lib/instalar_plugin.sh
```

Esto copia el plugin a `/usr/lib/x86_64-linux-gnu/wireshark/plugins/`.  
Luego reiniciar Wireshark. El protocolo aparecerá como **RFTP** en el panel de captura.

---
