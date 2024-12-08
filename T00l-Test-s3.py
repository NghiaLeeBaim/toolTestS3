import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import boto3
import threading
import os
import time


def test_upload(s3_client, bucket_name, file_path):
    try:
        file_size = os.path.getsize(file_path)
        start_time = time.time()

        with open(file_path, 'rb') as data:
            s3_client.upload_fileobj(
                data, bucket_name, os.path.basename(file_path))

        elapsed_time = time.time() - start_time
        upload_speed = (file_size / elapsed_time) / (1024 * 1024)  # MB/s
        return f"Tải lên hoàn tất trong {elapsed_time:.2f} giây ở tốc độ {upload_speed:.2f} MB/s"
    except Exception as e:
        return f"Tải lên thất bại: {str(e)}"


def test_download(s3_client, bucket_name, file_name, download_path):
    try:
        start_time = time.time()
        s3_client.download_file(bucket_name, file_name, download_path)
        elapsed_time = time.time() - start_time

        file_size = os.path.getsize(download_path)
        download_speed = (file_size / elapsed_time) / (1024 * 1024)  # MB/s
        return f"Tải xuống hoàn tất trong {elapsed_time:.2f} giây ở tốc độ {download_speed:.2f} MB/s"
    except Exception as e:
        return f"Tải xuống thất bại: {str(e)}"


def perform_test():
    global stop_requested
    stop_requested = False

    endpoint = endpoint_entry.get()
    access_key = access_key_entry.get()
    secret_key = secret_key_entry.get()
    region = region_entry.get()
    bucket_name = bucket_entry.get()
    file_path = file_path_var.get()

    if not all([endpoint, access_key, secret_key, region, bucket_name, file_path]):
        messagebox.showerror(
            "Lỗi", "Vui lòng điền đầy đủ thông tin và chọn tệp.")
        return

    if os.path.getsize(file_path) > 1 * 1024 * 1024 * 1024:  # 1 GB limit
        messagebox.showerror("Lỗi", "Kích thước tệp vượt quá giới hạn 1GB.")
        return

    progress_bar.grid(row=8, columnspan=2, pady=10)
    progress_bar.start()

    try:
        session = boto3.session.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3_client = session.client('s3', endpoint_url=f'https://{endpoint}')

        def run_test():
            try:
                if not stop_requested:
                    upload_result = test_upload(
                        s3_client, bucket_name, file_path)
                else:
                    return

                if not stop_requested:
                    download_file_name = os.path.basename(file_path)
                    download_path = os.path.join(
                        os.path.dirname(file_path), f"downloaded_{download_file_name}")
                    download_result = test_download(
                        s3_client, bucket_name, download_file_name, download_path)
                else:
                    return

                if not stop_requested:
                    combined_result = f"{upload_result}\n{download_result}"
                    messagebox.showinfo("Kết quả kiểm tra", combined_result)
            finally:
                progress_bar.stop()
                progress_bar.grid_remove()

        threading.Thread(target=run_test).start()

    except Exception as e:
        progress_bar.stop()
        progress_bar.grid_remove()
        messagebox.showerror("Lỗi", f"Không thể kết nối tới S3: {str(e)}")


def stop_test():
    global stop_requested
    stop_requested = True
    progress_bar.stop()
    progress_bar.grid_remove()
    messagebox.showinfo("Đã dừng", "Quá trình kiểm tra đã bị dừng.")


def select_file():
    file_path = filedialog.askopenfilename()
    file_path_var.set(file_path)
    file_label.config(text=os.path.basename(file_path))


# GUI
root = tk.Tk()
root.title("Kiểm tra băng thông S3")
root.geometry("500x400")
style = ttk.Style()
style.theme_use("clam")

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

# Input fields
ttk.Label(frame, text="Endpoint:").grid(row=0, column=0, sticky="w", pady=5)
endpoint_entry = ttk.Entry(frame, width=40)
endpoint_entry.grid(row=0, column=1)

ttk.Label(frame, text="Access Key:").grid(row=1, column=0, sticky="w", pady=5)
access_key_entry = ttk.Entry(frame, width=40)
access_key_entry.grid(row=1, column=1)

ttk.Label(frame, text="Secret Key:").grid(row=2, column=0, sticky="w", pady=5)
secret_key_entry = ttk.Entry(frame, width=40, show="*")
secret_key_entry.grid(row=2, column=1)

ttk.Label(frame, text="Region:").grid(row=3, column=0, sticky="w", pady=5)
region_entry = ttk.Entry(frame, width=40)
region_entry.grid(row=3, column=1)

ttk.Label(frame, text="Bucket Name:").grid(row=4, column=0, sticky="w", pady=5)
bucket_entry = ttk.Entry(frame, width=40)
bucket_entry.grid(row=4, column=1)

file_path_var = tk.StringVar()
ttk.Label(frame, text="Chọn tệp:").grid(row=5, column=0, sticky="w", pady=5)
file_button = ttk.Button(frame, text="Duyệt", command=select_file)
file_button.grid(row=5, column=1, sticky="w")
file_label = ttk.Label(frame, text="", width=40, anchor="w")
file_label.grid(row=6, column=1, sticky="w")

# Buttons
run_button = ttk.Button(frame, text="Bắt đầu kiểm tra", command=perform_test)
run_button.grid(row=7, column=0, pady=10)

stop_button = ttk.Button(frame, text="Dừng kiểm tra", command=stop_test)
stop_button.grid(row=7, column=1, pady=10)

# Progress bar
progress_bar = ttk.Progressbar(frame, orient="horizontal",
                               mode="indeterminate", length=300)
progress_bar.grid_remove()

stop_requested = False

root.mainloop()
