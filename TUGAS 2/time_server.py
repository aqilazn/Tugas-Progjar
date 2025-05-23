from socket import *
import socket
import threading
import logging
from datetime import datetime

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        threading.Thread.__init__(self)
        self.connection = connection
        self.address = address

    def run(self):
        while True:
            try:
                data = self.connection.recv(1024)
                if not data:
                    break

                pesan = data.decode('utf-8', errors='ignore')
                logging.warning(f"Diterima dari {self.address}: {repr(pesan)}")

                if pesan == "TIME\r\n":
                    now = datetime.now()
                    waktu = now.strftime("%H:%M:%S")
                    response = f"JAM {waktu}\r\n"
                    self.connection.sendall(response.encode())
                elif pesan == "QUIT\r\n":
                    logging.warning(f"Client {self.address} keluar")
                    break
                else:
                    self.connection.sendall(b"PERINTAH TIDAK DIKENALI\r\n")

            except Exception as e:
                logging.error(f"Error dari {self.address}: {e}")
                break

        self.connection.close()
        logging.warning(f"Koneksi dengan {self.address} ditutup")


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.my_socket.bind(('0.0.0.0', 45000))
        self.my_socket.listen(5)
        logging.warning("Server berjalan di port 45000...")

        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"Ada koneksi dari {client_address}")

            client_thread = ProcessTheClient(connection, client_address)
            client_thread.start()
            self.the_clients.append(client_thread)


def main():
    logging.basicConfig(level=logging.WARNING)
    svr = Server()
    svr.start()

if __name__ == "__main__":
    main()
