
#Implementar clase segmento, similar al TCP pero con menos parametros

class Segment:

	def __init__(self, src_port, dest_port):
		self.src_port = src_port
		self.dest_port = dest_port