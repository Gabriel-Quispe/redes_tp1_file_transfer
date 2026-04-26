import threading
import socket
import time
from src.lib.model.ftp.segment.segment import Segment
from src.lib.model.ftp.segment.const import OP_START_UPLOAD

def test_envio_y_recepcion():
    received = []

    # --- servidor en un hilo ---
    def run_server():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 65535))
        sock.settimeout(2)
        try:
            data, _ = sock.recvfrom(2000)
            segment = Segment.unpack(data)
            received.append(segment)
        except TimeoutError:
            pass
        finally:
            sock.close()

    # arranca el servidor en segundo plano
    t = threading.Thread(target=run_server)
    t.start()
    time.sleep(0.1)  # espera que el servidor esté listo

    # --- cliente ---
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = b"TEST de protocolo"
    segment = Segment(OP_START_UPLOAD, seq_num=1, wsize=10, payload=msg)
    sock.sendto(segment.pack(), ('127.0.0.1', 65535))
    sock.close()

    t.join()

    # --- verificaciones ---
    assert len(received) == 1
    assert received[0].opcode == OP_START_UPLOAD
    assert received[0].seq_num == 1
    assert received[0].payload == msg