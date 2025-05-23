import socket
import json
import base64
import logging

server_address = ('0.0.0.0', 8889)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message: {command_str[:30]}...")  # truncate if long
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(4096)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return False

def remote_list():
    command_str = "LIST"
    hasil = send_command(command_str)
    if hasil['status'] == 'OK':
        print("Daftar file:")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal:", hasil['data'])
        return False

def remote_get(filename=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil['status'] == 'OK':
        namafile = hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        with open(namafile, 'wb+') as fp:
            fp.write(isifile)
        print(f"File '{namafile}' berhasil diunduh")
        return True
    else:
        print("Gagal:", hasil['data'])
        return False

def remote_upload(local_filename, target_filename=""):
    if target_filename == "":
        target_filename = local_filename
    try:
        with open(local_filename, 'rb') as fp:
            content_b64 = base64.b64encode(fp.read()).decode()
        command_str = f"UPLOAD {target_filename} {content_b64}"
        hasil = send_command(command_str)
        if hasil['status'] == 'OK':
            print(f"File '{target_filename}' berhasil diupload")
            return True
        else:
            print("Gagal upload:", hasil['data'])
            return False
    except Exception as e:
        print(f"Gagal membaca file: {e}")
        return False

def remote_delete(filename):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil['status'] == 'OK':
        print(f"File '{filename}' berhasil dihapus")
        return True
    else:
        print("Gagal hapus:", hasil['data'])
        return False

if __name__ == '__main__':
    server_address = ('172.16.16.101', 8889)
    remote_upload('files/donalbebek.jpg')   # Upload
    remote_list()                     # List
    remote_get('donalbebek.jpg')      # Get
    remote_delete('donalbebek.jpg')   # Delete
