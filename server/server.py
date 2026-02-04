import socket
import threading
from config import HOST, PORT, LOG_FILE
from client_handler import handle_client

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER] Aktif di {HOST}:{PORT}")

    while True:
        client_socket, address = server.accept()
        print(f"[KONEKSI] {address} terhubung")

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, address, LOG_FILE)
        )
        thread.start()

start_server()
