import time
import csv
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from file_client_cli import remote_upload, remote_get

SERVER_ADDRESS = ('172.16.16.101', 8889)  # Sesuaikan IP sesuai server kamu
FILE_SIZES_MB = [10, 50, 100]
WORKER_COUNTS = [1, 5, 50]
OPERATIONS = ['UPLOAD', 'DOWNLOAD']
SERVER_WORKER_POOL_SIZES = [1, 5, 50]

def generate_dummy_file(filename, size_mb):
    if not os.path.exists(filename):
        print(f"[DEBUG] Membuat dummy file {filename} sebesar {size_mb} MB")
        with open(filename, 'wb') as f:
            f.write(os.urandom(size_mb * 1024 * 1024))
    else:
        print(f"[DEBUG] File dummy sudah ada: {filename}")

def client_task(op, size_mb, idx):
    filename = f"files/{size_mb}mb.dat"
    target_name = f"client_{idx}_{size_mb}mb.dat"
    print(f"[DEBUG] Client {idx} mulai {op} file {target_name} ({size_mb}MB)")
    start = time.time()
    if op == 'UPLOAD':
        success = remote_upload(filename, target_name)
    else:
        success = remote_get(target_name)
    end = time.time()
    elapsed = end - start
    throughput = (size_mb * 1024 * 1024) / elapsed if success else 0
    print(f"[DEBUG] Client {idx} selesai {op} file {target_name} - success: {success}, waktu: {elapsed:.2f}s")
    return (success, elapsed, throughput)

def run_stress(op, size_mb, client_workers, server_workers, mode='thread'):
    print(f"[INFO] Menjalankan stress test: operasi={op}, size={size_mb}MB, client_workers={client_workers}, server_workers={server_workers}, mode={mode}")
    results = []
    pool = ThreadPoolExecutor if mode == 'thread' else ProcessPoolExecutor

    with pool(max_workers=client_workers) as executor:
        futures = [executor.submit(client_task, op, size_mb, i) for i in range(client_workers)]
        for future in futures:
            try:
                success, elapsed, throughput = future.result()
                results.append((success, elapsed, throughput))
            except Exception as e:
                print(f"[ERROR] Exception di client task: {e}")
                results.append((False, 0, 0))
    return results

def main():
    os.makedirs("files", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    for size in FILE_SIZES_MB:
        generate_dummy_file(f"files/{size}mb.dat", size)

    output_csv = "results/server_threadpool.csv"  # atau nama sesuai mode
    with open(output_csv, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "No", "Operasi", "Volume (MB)",
            "Client Workers", "Server Workers",
            "Rata-rata Waktu (s)", "Rata-rata Throughput (Bps)",
            "Client Success", "Client Fail"
        ])
        csvfile.flush()  # 🟢 tambahkan ini agar header langsung ditulis

        no = 1
        for op in OPERATIONS:
            for size_mb in FILE_SIZES_MB:
                for client_w in WORKER_COUNTS:
                    for server_w in SERVER_WORKER_POOL_SIZES:
                        print(f"[{no}] {op} {size_mb}MB | client_workers={client_w} | server_workers={server_w}")

                        results = run_stress(op, size_mb, client_w, server_w, mode='thread')

                        total_time = sum(r[1] for r in results if r[0])
                        total_throughput = sum(r[2] for r in results if r[0])
                        success_count = sum(1 for r in results if r[0])
                        fail_count = len(results) - success_count
                        avg_time = total_time / success_count if success_count else 0
                        avg_throughput = total_throughput / success_count if success_count else 0

                        writer.writerow([
                            no, op, size_mb, client_w, server_w,
                            round(avg_time, 4), round(avg_throughput, 2),
                            success_count, fail_count
                        ])
                        csvfile.flush()  # 🟢 flush setiap baris agar hasil tidak hilang jika program berhenti
                        no += 1

if __name__ == "__main__":
    print("Menunggu server siap...")
    time.sleep(5)
    main()
