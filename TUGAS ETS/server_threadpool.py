import socket
import json
import base64
from concurrent.futures import ThreadPoolExecutor
import os
import argparse

HOST = '0.0.0.0'
PORT = 8889

FILES_DIR = "server_files"
os.makedirs(FILES_DIR, exist_ok=True)

def send_response(conn, response_dict):
    try:
        response_json = json.dumps(response_dict) + "\r\n\r\n"
        conn.sendall(response_json.encode())
    except Exception as e:
        print(f"[ERROR] send_response gagal: {e}")

def recv_command(conn):
    buffer = ""
    while True:
        try:
            data = conn.recv(8192)
            if not data:
                break
            buffer += data.decode(errors='ignore')

            if "\r\n\r\n" in buffer:
                payload = buffer.split("\r\n\r\n")[0]
                try:
                    result = json.loads(payload)
                    print(f"[DEBUG] JSON berhasil didecode, keys: {list(result.keys())}")
                    return result
                except json.JSONDecodeError:
                    # JSON belum lengkap, tunggu data lagi
                    continue
        except Exception as e:
            print(f"[ERROR] Error recv: {e}")
            break

    print("[ERROR] Gagal menerima atau decode JSON")
    return None


def handle_client(conn, addr):
    print(f"[DEBUG] Mulai tangani client {addr}")
    try:
        command = recv_command(conn)
        if command is None:
            conn.close()
            return

        action = command.get('action', '').upper()
        print(f"[DEBUG] Received action: {action} dari {addr}")

        if action == 'LIST':
            files = os.listdir(FILES_DIR)
            send_response(conn, {'status': 'OK', 'data': files})

        elif action == 'GET':
            filename = command.get('filename')
            filepath = os.path.join(FILES_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    content_b64 = base64.b64encode(f.read()).decode()
                send_response(conn, {
                    'status': 'OK',
                    'data_namafile': filename,
                    'data_file': content_b64
                })
            else:
                send_response(conn, {'status': 'ERROR', 'data': 'File not found'})

        elif action == 'UPLOAD':
            filename = command.get('filename')
            filedata_b64 = command.get('filedata')
            if not filename or not filedata_b64:
                send_response(conn, {'status': 'ERROR', 'data': 'Invalid upload data'})
            else:
                try:
                    filedata = base64.b64decode(filedata_b64)
                    with open(os.path.join(FILES_DIR, filename), 'wb') as f:
                        f.write(filedata)
                    send_response(conn, {'status': 'OK', 'data': f'File {filename} uploaded'})
                except Exception as e:
                    send_response(conn, {'status': 'ERROR', 'data': str(e)})

        elif action == 'DELETE':
            filename = command.get('filename')
            filepath = os.path.join(FILES_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                send_response(conn, {'status': 'OK', 'data': f'File {filename} deleted'})
            else:
                send_response(conn, {'status': 'ERROR', 'data': 'File not found'})

        else:
            send_response(conn, {'status': 'ERROR', 'data': 'Unknown command'})

    except Exception as e:
        print(f"[ERROR] Exception handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"[DEBUG] Koneksi ditutup dengan client {addr}")

def main():
    parser = argparse.ArgumentParser(description="ThreadPool Server")
    parser.add_argument("--workers", type=int, default=50,
                        help="Jumlah thread worker (default: 50)")
    args = parser.parse_args()

    print(f"Starting ThreadPool server with {args.workers} workers...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("Server listening on", s.getsockname())
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            while True:
                print("[DEBUG] Menunggu koneksi...")
                conn, addr = s.accept()
                print(f"[DEBUG] Menerima koneksi dari {addr}")
                executor.submit(handle_client, conn, addr)

if __name__ == '__main__':
    main()
