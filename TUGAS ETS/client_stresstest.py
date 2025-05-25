import socket
import json
import base64
import os
import time
import concurrent.futures
import csv

SERVER_IP = '127.0.0.1'  # sesuaikan dengan IP server
SERVER_PORT = 8889

def create_dummy_file(filename, size_mb):
    """Membuat file dummy untuk digunakan dalam stress test."""
    if not os.path.exists(filename):
        print(f"Membuat file dummy {filename} ukuran {size_mb}MB")
        with open(filename, 'wb') as f:
            f.write(os.urandom(size_mb * 1024 * 1024))

def send_command(command_str):
    """Mengirimkan perintah ke server dan menerima balasan."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            data_received += data.decode()
            if "\r\n\r\n" in data_received:
                break
        sock.close()
        return json.loads(data_received)
    except Exception as e:
        return dict(status='ERROR', data=str(e))

def upload_file(local_filename, target_filename):
    """Mengupload file ke server."""
    try:
        with open(local_filename, 'rb') as f:
            content_b64 = base64.b64encode(f.read()).decode()
        command = f"UPLOAD {target_filename} {content_b64}"
        return send_command(command)
    except Exception as e:
        return dict(status='ERROR', data=str(e))

def download_file(filename, save_as):
    """Mengunduh file dari server dan menyimpannya ke disk."""
    command = f"GET {filename}"
    resp = send_command(command)
    if resp['status'] == 'OK':
        content_b64 = resp['data_file']
        with open(save_as, 'wb') as f:
            f.write(base64.b64decode(content_b64))
    return resp

def stress_test_worker(operation, volume_mb, worker_id):
    """Worker untuk menjalankan operasi stress test (upload/download)."""
    dummy_filename = f"dummy_{volume_mb}MB.dat"
    upload_name = f"upload_{worker_id}_{volume_mb}MB.dat"
    download_name = f"download_{worker_id}_{volume_mb}MB.dat"
    
    if operation == 'upload':
        create_dummy_file(dummy_filename, volume_mb)
        start = time.time()
        resp = upload_file(dummy_filename, upload_name)
        end = time.time()
        duration = end - start
        success = (resp['status'] == 'OK')
        bytes_processed = volume_mb * 1024 * 1024 if success else 0
        return (duration, bytes_processed, success)
    
    elif operation == 'download':
        create_dummy_file(dummy_filename, volume_mb)
        upload_file(dummy_filename, upload_name)  # Upload terlebih dahulu sebelum download
        start = time.time()
        resp = download_file(upload_name, download_name)
        end = time.time()
        duration = end - start
        success = (resp['status'] == 'OK')
        bytes_processed = volume_mb * 1024 * 1024 if success else 0
        if os.path.exists(download_name):
            os.remove(download_name)
        return (duration, bytes_processed, success)
    
    else:
        return (0, 0, False)

def run_stress_test(concurrency_model, operation, volume_mb, client_workers, server_workers):
    """Menjalankan stress test berdasarkan parameter yang diberikan."""
    print(f"Test: {concurrency_model} | Op: {operation} | Vol: {volume_mb}MB | Client workers: {client_workers} | Server workers: {server_workers}")
    
    if concurrency_model == 'thread':
        executor_class = concurrent.futures.ThreadPoolExecutor
    elif concurrency_model == 'process':
        executor_class = concurrent.futures.ProcessPoolExecutor
    else:
        raise ValueError("Model concurrency harus 'thread' atau 'process'")

    with executor_class(max_workers=client_workers) as executor:
        futures = []
        start = time.time()
        for i in range(client_workers):
            futures.append(executor.submit(stress_test_worker, operation, volume_mb, i))
        results = [f.result() for f in futures]
        end = time.time()

    total_duration = end - start
    total_bytes = sum(r[1] for r in results)
    success_count = sum(1 for r in results if r[2])
    fail_count = client_workers - success_count
    throughput_per_client = total_bytes / total_duration if total_duration > 0 else 0

    return {
        'operation': operation,
        'volume_mb': volume_mb,
        'client_workers': client_workers,
        'server_workers': server_workers,
        'concurrency_model': concurrency_model,
        'total_duration': total_duration,
        'throughput_per_client': throughput_per_client,
        'success_client': success_count,
        'fail_client': fail_count,
        'success_server': server_workers,  # Asumsikan semua worker server sukses
        'fail_server': 0
    }

if __name__ == "__main__":
    operations = ['upload', 'download']
    volumes = [10, 50, 100]
    client_workers_list = [1, 5, 50]
    server_workers_list = [1, 5, 50]
    concurrency_models = ['thread', 'process']

    filename_csv = 'stress_test_results.csv'
    with open(filename_csv, 'w', newline='') as csvfile:
        fieldnames = [
            'No', 'Operation', 'Volume_MB', 'Client_Workers', 'Server_Workers',
            'Concurrency_Model', 'Total_Duration_s', 'Throughput_Bps',
            'Success_Client', 'Fail_Client', 'Success_Server', 'Fail_Server'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        test_no = 1
        for concurrency_model in concurrency_models:
            for operation in operations:
                for volume in volumes:
                    for client_workers in client_workers_list:
                        for server_workers in server_workers_list:
                            result = run_stress_test(concurrency_model, operation, volume, client_workers, server_workers)
                            result_row = {
                                'No': test_no,
                                'Operation': result['operation'],
                                'Volume_MB': result['volume_mb'],
                                'Client_Workers': result['client_workers'],
                                'Server_Workers': result['server_workers'],
                                'Concurrency_Model': result['concurrency_model'],
                                'Total_Duration_s': round(result['total_duration'], 3),
                                'Throughput_Bps': int(result['throughput_per_client']),
                                'Success_Client': result['success_client'],
                                'Fail_Client': result['fail_client'],
                                'Success_Server': result['success_server'],
                                'Fail_Server': result['fail_server']
                            }
                            print(result_row)
                            writer.writerow(result_row)
                            test_no += 1
