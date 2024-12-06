import tkinter as tk
from tkinter import filedialog, messagebox
import boto3
import threading
import time
import os
from tkinter import ttk


def test_upload(s3_client, bucket_name, file_path):
    try:
        file_size = os.path.getsize(file_path)
        start_time = time.time()

        with open(file_path, 'rb') as data:
            s3_client.upload_fileobj(
                data, bucket_name, os.path.basename(file_path))

        end_time = time.time()
        elapsed_time = end_time - start_time
        upload_speed = (file_size / elapsed_time) / (1024 * 1024)  # MB/s

        return f"Upload completed in {elapsed_time:.2f} seconds at {upload_speed:.2f} MB/s"
    except Exception as e:
        return f"Upload failed: {str(e)}"


def test_download(s3_client, bucket_name, file_name, download_path):
    try:
        start_time = time.time()

        s3_client.download_file(bucket_name, file_name, download_path)

        end_time = time.time()
        elapsed_time = end_time - start_time
        file_size = os.path.getsize(download_path)
        download_speed = (file_size / elapsed_time) / (1024 * 1024)  # MB/s

        return f"Download completed in {elapsed_time:.2f} seconds at {download_speed:.2f} MB/s"
    except Exception as e:
        return f"Download failed: {str(e)}"


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
            "Error", "Please fill in all fields and select a file.")
        return

    if os.path.getsize(file_path) > 1 * 1024 * 1024 * 1024:  # 1 GB limit
        messagebox.showerror("Error", "File size exceeds 1GB limit.")
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
                # Perform upload test
                if not stop_requested:
                    upload_result = test_upload(
                        s3_client, bucket_name, file_path)
                else:
                    return

                # Perform download test
                if not stop_requested:
                    download_file_name = os.path.basename(file_path)
                    download_path = os.path.join(os.path.dirname(
                        file_path), f"downloaded_{download_file_name}")
                    download_result = test_download(
                        s3_client, bucket_name, download_file_name, download_path)
                else:
                    return

                if not stop_requested:
                    # Display results
                    combined_result = f"{upload_result}\n{download_result}"
                    messagebox.showinfo("Test Results", combined_result)
            finally:
                progress_bar.stop()
                progress_bar.grid_remove()

        threading.Thread(target=run_test).start()

    except Exception as e:
        progress_bar.stop()
        progress_bar.grid_remove()
        messagebox.showerror("Error", f"Failed to connect to S3: {str(e)}")


def stop_test():
    global stop_requested
    stop_requested = True
    progress_bar.stop()
    progress_bar.grid_remove()
    messagebox.showinfo("Test Stopped", "The test has been stopped.")


def select_file():
    file_path = filedialog.askopenfilename()
    file_path_var.set(file_path)
    file_label.config(text=os.path.basename(file_path))


# Create the GUI window
root = tk.Tk()
root.title("S3 Bandwidth Test")

# Define input fields
frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

tk.Label(frame, text="Endpoint:").grid(row=0, column=0, sticky="w")
endpoint_entry = tk.Entry(frame, width=40)
endpoint_entry.grid(row=0, column=1)

tk.Label(frame, text="Access Key:").grid(row=1, column=0, sticky="w")
access_key_entry = tk.Entry(frame, width=40)
access_key_entry.grid(row=1, column=1)

tk.Label(frame, text="Secret Key:").grid(row=2, column=0, sticky="w")
secret_key_entry = tk.Entry(frame, width=40, show="*")
secret_key_entry.grid(row=2, column=1)

tk.Label(frame, text="Region:").grid(row=3, column=0, sticky="w")
region_entry = tk.Entry(frame, width=40)
region_entry.grid(row=3, column=1)

tk.Label(frame, text="Bucket Name:").grid(row=4, column=0, sticky="w")
bucket_entry = tk.Entry(frame, width=40)
bucket_entry.grid(row=4, column=1)

file_path_var = tk.StringVar()
tk.Label(frame, text="Select File:").grid(row=5, column=0, sticky="w")
file_button = tk.Button(frame, text="Browse", command=select_file)
file_button.grid(row=5, column=1, sticky="w")
file_label = tk.Label(frame, text="", width=40, anchor="w")
file_label.grid(row=6, column=1, sticky="w")

run_button = tk.Button(frame, text="Run Test", command=perform_test)
run_button.grid(row=7, column=0, pady=10)

stop_button = tk.Button(frame, text="Stop Test", command=stop_test)
stop_button.grid(row=7, column=1, pady=10)

progress_bar = ttk.Progressbar(
    frame, orient="horizontal", mode="indeterminate", length=300)
progress_bar.grid_remove()

stop_requested = False

root.mainloop()
