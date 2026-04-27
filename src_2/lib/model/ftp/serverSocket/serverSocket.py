
#implementar clase serverSocket



"""
from socket import *
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(("", serverPort))
print("The server is ready to receive")
message = ""
while message != "close":
	message, clientAddress = serverSocket.recvfrom(2048)
	message = message.decode()
	print("Mensaje recibido: " + message)
	serverSocket.sendto(message.encode(), clientAddress)
serverSocket.close()
"""