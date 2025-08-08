import os
import asyncio
import httpx
import pandas as pd
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from datetime import datetime

# === Фикс для поиска Tcl/Tk ===
os.environ["TCL_LIBRARY"] = r"C:\Users\User\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
os.environ["TK_LIBRARY"] = r"C:\Users\User\AppData\Local\Programs\Python\Python313\tcl\tk8.6"

# === Настройки ===
BASE_URL = "https://admin-gc.learning.samolet.ru/api/v1/topic/block/result/export"
TOPIC_TYPE_ID = 15
TIMEOUT = 120

stop_flag = False

# === Асинхронная логика ===
async def download_file(client, topic_id, save_dir, headers, log_callback, progress_var, total, current):
    url = f"{BASE_URL}?topicId={topic_id}&topicTypeId={TOPIC_TYPE_ID}"
    for attempt in range(3):
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                content = response.content
                text_start = content[:200].decode('utf-8', errors='ignore')
                ext = ".csv" if text_start.startswith("Почта;") or ";" in text_start else ".xlsx"
                filename = os.path.join(save_dir, f"{topic_id}{ext}")
                with open(filename, "wb") as f:
                    f.write(content)
                log_callback(f"✅ {topic_id} → {filename}")
                break
            else:
                log_callback(f"❌ {topic_id}: HTTP {response.status_code}")
        except Exception as e:
            log_callback(f"⚠ Ошибка {topic_id}: {repr(e)}")
        await asyncio.sleep(3)
    else:
        log_callback(f"⛔ Не удалось скачать {topic_id}")

    current[0] += 1
    progress_var.set(int(current[0] / total * 100))

async def download_process(save_path, token_path, excel_path, log_callback, progress_var):
    try:
        with open(token_path, "r", encoding="utf-8") as f:
            token = f.read().strip()
    except Exception as e:
        log_callback(f"Ошибка чтения токена: {e}")
        return

    try:
        # Читаем ID, пропуская заголовок и нечисловые значения
        df = pd.read_excel(excel_path, header=None)
        IDS = []
        for val in df.iloc[:, 0]:
            try:
                IDS.append(int(val))
            except (ValueError, TypeError):
                continue  # пропускаем заголовки и пустые
    except Exception as e:
        log_callback(f"Ошибка чтения Excel: {e}")
        return

    if not IDS:
        log_callback("В Excel не найдено ни одного ID!")
        return

    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Referer": "https://admin-gc.learning.samolet.ru/"
    }

    os.makedirs(save_path, exist_ok=True)
    total = len(IDS)
    current = [0]

    log_callback(f"Найдено ID: {total}. Начинаем загрузку...")

    async with httpx.AsyncClient(verify=False, timeout=TIMEOUT) as client:
        for topic_id in IDS:
            if stop_flag:
                log_callback("Загрузка остановлена пользователем.")
                break
            await download_file(client, topic_id, save_path, headers, log_callback, progress_var, total, current)
            await asyncio.sleep(1)

    log_callback("✅ Загрузка завершена.")

# === GUI ===
def run_download():
    save_dir = save_path.get()
    token_file = token_path.get()
    excel_file = excel_path.get()
    if not save_dir or not token_file or not excel_file:
        messagebox.showerror("Ошибка", "Заполните все поля!")
        return

    progress_var.set(0)
    log_box.delete(1.0, tk.END)
    threading.Thread(target=lambda: asyncio.run(download_process(save_dir, token_file, excel_file, log_message, progress_var)), daemon=True).start()

def log_message(msg):
    log_box.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    log_box.see(tk.END)

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        save_path.set(folder)

def choose_token():
    file = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file:
        token_path.set(file)

def choose_excel():
    file = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file:
        excel_path.set(file)

def stop_download():
    global stop_flag
    stop_flag = True
    log_message("Остановка запрошена...")

# === Создание окна ===
root = tk.Tk()
root.title("Загрузка результатов курсов")
root.geometry("700x500")
root.configure(bg="#f4f4f4")
root.resizable(False, False)  # запрещаем растягивание окна

save_path = tk.StringVar()
token_path = tk.StringVar()
excel_path = tk.StringVar()
progress_var = tk.IntVar()

# Поля и кнопки (сетка)
tk.Label(root, text="Папка для сохранения:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=save_path, width=50).grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Обзор", command=choose_folder).grid(row=0, column=2, padx=10, pady=5)

tk.Label(root, text="Файл токена:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=token_path, width=50).grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="Обзор", command=choose_token).grid(row=1, column=2, padx=10, pady=5)

tk.Label(root, text="Excel с ID:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=excel_path, width=50).grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="Обзор", command=choose_excel).grid(row=2, column=2, padx=10, pady=5)

# Кнопки управления
tk.Button(root, text="Старт", command=run_download, bg="green", fg="white", width=10).grid(row=3, column=1, sticky="e", pady=10)
tk.Button(root, text="Стоп", command=stop_download, bg="red", fg="white", width=10).grid(row=3, column=2, sticky="w", pady=10)

# Прогресс
ttk.Progressbar(root, length=500, variable=progress_var).grid(row=4, column=0, columnspan=3, pady=10)

# Лог
log_box = scrolledtext.ScrolledText(root, width=80, height=15)
log_box.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()
