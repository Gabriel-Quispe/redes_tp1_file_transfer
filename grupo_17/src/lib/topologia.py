from mininet.topo import Topo
from mininet.node import OVSSwitch
from mininet.link import TCLink 

class TP2Topo(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        
        # failMode=standalone o hay errores de controlador
        s1 = self.addSwitch('s1', cls=OVSSwitch, failMode='standalone')        
        # Enlace normal a h1
        self.addLink(h1, s1)         
        # Hay que usar TCLink para que el loss se active
        self.addLink(h2, s1, cls=TCLink, loss=10)
        
        # H1 <-> S1 <-> H2

# Esto define las topologias para usar
topos = {'tp2': (lambda: TP2Topo())}