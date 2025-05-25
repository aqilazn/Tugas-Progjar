import socket
import logging
from multiprocessing import Pool, cpu_count
import os
from file_protocol import FileProtocol

fp = FileProtocol()

# Worker handler function must be top-level (picklable)
def handle_client_task(data):
    try:
        request, client_address = data
        logging.warning(f"processing request from {client_address}")
        response = fp.proses_string(request)
        return response
    except Exception as e:
        logging.error(f"Error handling request: {e}")
        return ""

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=8889, max_workers=None):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.max_workers = max_workers or cpu_count()
        self.pool = Pool(processes=self.max_workers)

    def run(self):
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(50)
        logging.warning(f"server listening on {self.ipinfo} with {self.max_workers} workers")
        try:
            while True:
                conn, addr = self.my_socket.accept()
                logging.warning(f"connection from {addr}")
                data = conn.recv(4096)
                if data:
                    request = data.decode()
                    result = self.pool.apply(handle_client_task, args=((request, addr),))
                    conn.sendall((result + "\r\n\r\n").encode())
                conn.close()
        except KeyboardInterrupt:
            logging.warning("server shutting down")
        finally:
            self.pool.close()
            self.pool.join()
            self.my_socket.close()

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.WARNING)
    max_workers = int(sys.argv[1]) if len(sys.argv) > 1 else None
    svr = Server(max_workers=max_workers)
    svr.run()
