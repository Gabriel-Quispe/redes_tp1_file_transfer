from .protocol_strategy import ProtocolStrategy
class SelectiveRepeat(ProtocolStrategy):
    def __init__(self, address, socket):
        super().__init__(address, socket)
        
    def set_window(self,tam:int):
        pass
    
    def send_data(self,payload):
        pass
    
    def receive_data():
        pass