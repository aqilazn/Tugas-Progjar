import socket
import json
import base64
import logging

logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(message)s')

# Default server address, bisa diubah di main atau di caller
SERVER_HOST = "172.16.16.101"
SERVER_PORT = 8889

def send_command(command_str="", host=SERVER_HOST, port=SERVER_PORT):
    server_address = (host, port)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(server_address)
            logging.warning(f"Connecting to {server_address}")
            logging.warning(f"Sending message: {command_str[:30]}...")  # truncate if panjang
            sock.sendall(command_str.encode())
            print("[DEBUG] Upload JSON sent, waiting for response")

            data_received = ""
            while True:
                data = sock.recv(4096)
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            hasil = json.loads(data_received.split("\r\n\r\n")[0])
            logging.warning("Data received from server:")
            return hasil
    except Exception as e:
        logging.warning(f"Error during data receiving: {e}")
        return {"status": "ERROR", "data": str(e)}

def remote_list(host=SERVER_HOST, port=SERVER_PORT):
    command = {"action": "LIST"}
    command_str = json.dumps(command) + "\r\n\r\n"
    hasil = send_command(command_str, host, port)
    if hasil.get('status') == 'OK':
        print("Daftar file:")
        for nmfile in hasil.get('data', []):
            print(f"- {nmfile}")
        return hasil
    else:
        print("Gagal:", hasil.get('data'))
        return hasil

def remote_get(filename="", host=SERVER_HOST, port=SERVER_PORT):
    command = {"action": "GET", "filename": filename}
    command_str = json.dumps(command) + "\r\n\r\n"
    hasil = send_command(command_str, host, port)
    if hasil.get('status') == 'OK':
        namafile = hasil.get('data_namafile', filename)
        try:
            isifile = base64.b64decode(hasil.get('data_file', ''))
            with open(namafile, 'wb+') as fp:
                fp.write(isifile)
            print(f"File '{namafile}' berhasil diunduh")
            return hasil
        except Exception as e:
            print(f"Gagal menulis file: {e}")
            return {"status": "ERROR", "data": str(e)}
    else:
        print("Gagal:", hasil.get('data'))
        return hasil

def remote_upload(local_filename, target_filename="", host=SERVER_HOST, port=SERVER_PORT):
    if target_filename == "":
        target_filename = local_filename
    try:
        with open(local_filename, 'rb') as fp:
            content_b64 = base64.b64encode(fp.read()).decode()
        command = {
            "action": "UPLOAD",
            "filename": target_filename,
            "filedata": content_b64
        }
        command_str = json.dumps(command) + "\r\n\r\n"
        hasil = send_command(command_str, host, port)
        if hasil.get('status') == 'OK':
            print(f"File '{target_filename}' berhasil diupload")
            return hasil
        else:
            print("Gagal upload:", hasil.get('data'))
            return hasil
    except Exception as e:
        print(f"Gagal membaca file: {e}")
        return {"status": "ERROR", "data": str(e)}

def remote_delete(filename, host=SERVER_HOST, port=SERVER_PORT):
    command = {"action": "DELETE", "filename": filename}
    command_str = json.dumps(command) + "\r\n\r\n"
    hasil = send_command(command_str, host, port)
    if hasil.get('status') == 'OK':
        print(f"File '{filename}' berhasil dihapus")
        return hasil
    else:
        print("Gagal hapus:", hasil.get('data'))
        return hasil

if __name__ == '__main__':
    # Contoh pemanggilan fungsi
    remote_upload('files/donalbebek.jpg')
    remote_list()
    remote_get('donalbebek.jpg')
    remote_delete('donalbebek.jpg')
