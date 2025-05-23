import socket

server_address = ('172.16.16.101', 45000)  # IP mesin-1
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server_address)

try:
    while True:
        pesan = input("Ketik TIME atau QUIT: ")
        kirim = pesan + "\r\n"
        sock.sendall(kirim.encode())

        data = sock.recv(1024)
        print("Dari server:", data.decode())

        if pesan == "QUIT":
            break
finally:
    sock.close()
