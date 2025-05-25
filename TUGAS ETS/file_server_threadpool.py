import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from file_protocol import FileProtocol

fp = FileProtocol()

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=8889, max_workers=10):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def handle_client(self, connection, address):
        logging.warning(f"handling client {address}")
        try:
            while True:
                data = b''
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if b"\r\n\r\n" in data:
                        break
                if not data:
                    break
                request = data.decode().strip()
                response = fp.proses_string(request)
                connection.sendall((response + "\r\n\r\n").encode())
        except Exception as e:
            logging.error(f"error with client {address}: {e}")
        finally:
            connection.close()


    def run(self):
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(50)
        logging.warning(f"server listening on {self.ipinfo}")
        try:
            while True:
                conn, addr = self.my_socket.accept()
                logging.warning(f"connection from {addr}")
                self.executor.submit(self.handle_client, conn, addr)
        except KeyboardInterrupt:
            logging.warning("server shutdown")
        finally:
            self.executor.shutdown()
            self.my_socket.close()

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.WARNING)
    max_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    svr = Server(max_workers=max_workers)
    svr.run()
