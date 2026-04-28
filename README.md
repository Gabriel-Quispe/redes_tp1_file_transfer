# TP N°1 Redes: File Transfer

Creación de una aplicación de red, buscando comprender cómo se comunican los procesos a través de la red, y cuál es el modelo de servicio que la capa de transporte le ofrece a la capa de aplicación y aprender el uso de la interfaz de sockets y los principios básicos de la transferencia de datos confiable.

# Guia de ejecución de pruebas
1. Desde la raiz del proyecto, ejecutar:
```
sudo mn --custom ./topologia.py --topo tp2 --mac --switch ovsk --controller none
```
2. Una vez dentro de mininet, crear dos terminales para cada host y una instancia de wireshark:
```
xterm h1 h2
h1 wireshark &

```
3. (__*Provisional*__) Ejecutar cliente o servidor en cada host, por ejemplo si h1 es el cliente y h2 el servidor:

__En h2__:
Levanto el servidor en la direccion 10.0.0.2:65535 con la carpeta de descargas en ./storage
```
python3 src/start-server -H 10.0.0.2 -p 65535 -s storage -v
 ```

__En h1__:
pruebo enviar un archivo pesado.jpg cuyo nombre en el server será prueba_server.jpg, usando el protocolo 1 (stop n wait), de manera verbosa
```
python3 src/upload -H 10.0.0.2 -p 65535 -s pesado.jpg  -n prueba_server.jpg -r 1 -v

 ```
Para que Wireshark detecte el protocolo RFTP dentro de mininet, hay que copiar el plugin a esta direccion:
```
sudo cp plugin_wireshark.lua /usr/lib/x86_64-linux-gnu/wireshark/plugins/
```
**Participantes:**
1. 
2. 
3. 
4. 
5. 
