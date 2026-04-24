# TP N°1 Redes: File Transfer

Creación de una aplicación de red, buscando comprender cómo se comunican los procesos a través de la red, y cuál es el modelo de servicio que la capa de transporte le ofrece a la capa de aplicación y aprender el uso de la interfaz de sockets y los principios básicos de la transferencia de datos confiable.

# Guia de ejecución de pruebas
1. Desde la raiz del proyecto, ejecutar:
```
sudo mn --custom ./topologia.py --topo tp2 --mac --switch ovsk --controller none
```
2. Una vez dentro de mininet, crear dos terminales para cada host:
```
xterm h1 h2
```
3. (__*Provisional*__) Ejecutar cliente o servidor en cada host, por ejemplo si h1 es el cliente y h2 el servidor:

__En h2__:
```
python3 start-server.py
 ```
__En h1__:
```
python3 upload.py
 ```
**Participantes:**
1. 
2. 
3. 
4. 
5. 
