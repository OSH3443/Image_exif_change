import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import concurrent.futures
import threading
import multiprocessing
import exiftool
from delay_time import add_delay, delay_generator, check_time

# 7. 하위 폴더의 이미지 파일들의 경로를 찾아서 리스트에 저장하는 함수
def get_image_files(subfolder_path: str, extensions: list) -> list:
    image_files_paths = []
    with os.scandir(subfolder_path) as entries:
        for entry in entries:
            if entry.is_file() and any(entry.name.lower().endswith(ext) for ext in extensions):
                image_files_paths.append(entry.path)
    # 파일 이름을 기준으로 오름차순 정렬
    image_files_paths.sort()
    return image_files_paths


# exif를 수정할 함수
def change_file_exif(subfolder_path: str, new_date: str, image_extensions: list, delay_ratio: dict, progress_queue,
                     stop_event):
    # 8. 폴더 내부의 이미지 파일 주소 리스트
    subfolder_image_file_paths = get_image_files(subfolder_path, image_extensions)
    total_files = len(subfolder_image_file_paths)
    print(f"[change_file_exif]\n{subfolder_path}의 이미지 리스트 ({total_files}개)\n{subfolder_image_file_paths}")

    # 7. 이 폴더에서 exif 수정할 exiftool 열기
    with exiftool.ExifTool() as et:
        # 10. 이미지 파일 주소 중 하나 불러오기
        for idx, image_file_path in enumerate(subfolder_image_file_paths):
            if stop_event.is_set():
                print(f"Process stopped for {subfolder_path}")
                break

            # 11. 이미지 파일 주소의 exif 변경
            command = ["-overwrite_original",
                       "-AllDates=" + new_date,
                       "-FileModifyDate=" + new_date,
                       image_file_path]
            encoded_command = [arg.encode('cp949') for arg in command]
            print(f"[change_file_exif] {idx + 1} : [{image_file_path}]\n{encoded_command}")

            # 14. 반복된 모든 명령어를 실행하고 exiftool 종료
            et.execute(*encoded_command)

            # 12. index가 홀수라면 날짜에 delay를 생성하여 더해줌
            if idx & 1:
                new_date = add_delay(new_date, delay_generator(delay_ratio))

            # 업데이트된 진행 상황을 큐에 추가
            progress_queue.put((subfolder_path, idx + 1, total_files))


# GUI 코드 시작
def browse_folder():
    folder_path = filedialog.askdirectory()
    if not folder_path:
        return

    folder_path_entry.delete(0, tk.END)
    folder_path_entry.insert(0, folder_path)
    load_subfolders(folder_path)


def load_subfolders(folder_path):
    subfolders = [
        os.path.join(folder_path, name)
        for name in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, name))
    ]

    for widget in folder_frame.winfo_children():
        widget.destroy()

    global folder_vars
    folder_vars = {}
    for subfolder in subfolders:
        frame = ttk.Frame(folder_frame)
        var = tk.BooleanVar()
        cb = tk.Checkbutton(frame, text=subfolder, variable=var)
        cb.pack(side=tk.LEFT)
        date_entry = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2,
                               date_pattern='y-mm-dd')
        date_entry.pack(side=tk.LEFT, padx=5)
        time_entry = ttk.Entry(frame, width=10)
        time_entry.pack(side=tk.LEFT, padx=5)
        time_format_label = ttk.Label(frame, text="(HH:MM:SS)")
        time_format_label.pack(side=tk.LEFT, padx=5)
        progress_bar = ttk.Progressbar(frame, length=200)
        progress_bar.pack(side=tk.LEFT, padx=5)
        progress_label = ttk.Label(frame, text="0/0")
        progress_label.pack(side=tk.LEFT, padx=5)
        frame.pack(anchor='w', pady=2)
        folder_vars[subfolder] = (var, date_entry, time_entry, progress_bar, progress_label)


def submit():
    global stop_event
    stop_event.clear()

    delay_ratio = {2: 85, 3: 10, 4: 5}
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']

    selected_folders = {}
    for folder, (var, date_entry, time_entry, progress_bar, progress_label) in folder_vars.items():
        if var.get():
            date = date_entry.get_date().strftime('%Y:%m:%d')
            time_str = time_entry.get()
            if not validate_time_format(time_str):
                messagebox.showwarning("Warning",
                                       f"Please enter the time in the correct format (HH:MM:SS) for {folder}")
                return
            selected_folders[folder] = (f"{date} {time_str}", progress_bar, progress_label)

    if not selected_folders:
        messagebox.showwarning("Warning", "No folders selected")
        return

    start_time = time.perf_counter()
    manager = multiprocessing.Manager()
    progress_queue = manager.Queue()
    stop_event = manager.Event()

    def process_folders():
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = []
            for subfolder_path, (modify_datetime, progress_bar, progress_label) in selected_folders.items():
                futures.append(
                    executor.submit(change_file_exif, subfolder_path, modify_datetime, image_extensions, delay_ratio,
                                    progress_queue, stop_event))

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"오류 발생: 오류 메시지: {e}")

        end_time = time.perf_counter()
        print(check_time(start_time, end_time))
        messagebox.showinfo("Info", "Process completed successfully")

    threading.Thread(target=process_folders).start()
    root.after(100, update_progress, progress_queue, selected_folders)


def update_progress(progress_queue, folders):
    while not progress_queue.empty():
        subfolder_path, current, total = progress_queue.get()
        progress_bar, progress_label = folders[subfolder_path][1:3]
        progress_bar['value'] = (current / total) * 100
        progress_label.config(text=f"{current}/{total}")
        if current == total:
            progress_bar['value'] = 100

    if not stop_event.is_set():
        root.after(100, update_progress, progress_queue, folders)


def validate_time_format(time_str):
    try:
        time.strptime(time_str, '%H:%M:%S')
        return True
    except ValueError:
        return False


def stop_process():
    global stop_event
    stop_event.set()
    messagebox.showinfo("Info", "Process will stop after current file is processed")


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        stop_process()
        root.destroy()


if __name__ == "__main__":
    stop_event = multiprocessing.Event()

    root = tk.Tk()
    root.title("Modify EXIF Metadata")

    folder_path_entry = ttk.Entry(root, width=50)
    folder_path_entry.pack(padx=10, pady=5)

    browse_button = ttk.Button(root, text="Browse", command=browse_folder)
    browse_button.pack(padx=10, pady=5)

    folder_frame = ttk.Frame(root)
    folder_frame.pack(padx=10, pady=5, fill='x')

    submit_button = ttk.Button(root, text="Submit", command=submit)
    submit_button.pack(padx=10, pady=5)

    stop_button = ttk.Button(root, text="Stop", command=stop_process)
    stop_button.pack(padx=10, pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()
