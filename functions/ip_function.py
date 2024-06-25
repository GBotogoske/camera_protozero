import socket

def get_local_ip():
    # Tenta conectar a um endereço remoto (não precisa realmente se conectar)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Use um endereço público e um número de porta arbitrário
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip
