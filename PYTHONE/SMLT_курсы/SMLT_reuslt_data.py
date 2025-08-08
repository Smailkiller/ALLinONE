import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
import glob

def run_script(results_folder, questions_file):
    try:
        questions_df = pd.read_excel(questions_file, usecols=[0, 1], header=None)
        questions_df.columns = ["Вопрос", "Ссылка"]
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка чтения файла вопросов:\n{e}")
        return

    user_results = {}
    csv_files = glob.glob(os.path.join(results_folder, "*.csv"))

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path, sep=";", encoding="utf-8-sig", dtype=str)

            if df.shape[0] < 2 or df.iloc[1].isnull().all():
                continue

            if "Итог" not in df.columns:
                continue

            base_end = df.columns.get_loc("Итог") + 1
            question_columns = df.columns[base_end:]

            for idx, row in df.iterrows():
                if row.isnull().all():
                    continue

                user_key = (
                    row.get("Фамилия", "").strip(),
                    row.get("Имя", "").strip(),
                    row.get("Почта", "").strip()
                )

                if not user_key[0] and not user_key[1] and not user_key[2]:
                    continue

                if user_key not in user_results:
                    user_results[user_key] = {
                        "Фамилия": user_key[0],
                        "Имя": user_key[1],
                        "Почта": user_key[2],
                        "Результат": row.get("Результаты в процентах", ""),
                        "Итог": row.get("Итог", ""),
                        "Ответы": []
                    }

                for i in range(0, len(question_columns), 5):
                    block = question_columns[i:i + 5]
                    col_map = {col.lower(): col for col in block}

                    q_col = next((v for k, v in col_map.items() if "вопрос" in k), None)
                    a_col = next((v for k, v in col_map.items() if "ответ" in k), None)
                    r_col = next((v for k, v in col_map.items() if "правильность" in k), None)

                    if not q_col or not a_col or not r_col:
                        continue

                    question = row.get(q_col, "")
                    answer = row.get(a_col, "")
                    correct = row.get(r_col, "")

                    if pd.isna(question) or question.strip() == "":
                        continue

                    if str(correct).strip().lower() != "нет":
                        continue

                    match_row = questions_df[questions_df["Вопрос"].str.strip() == str(question).strip()]
                    link = match_row["Ссылка"].values[0] if not match_row.empty else ""

                    user_results[user_key]["Ответы"].append(
                        f"Вопрос: {question}\nОтвет: {answer}\nСсылка: {link}"
                    )

        except Exception:
            continue

    final_data = []
    for user_data in user_results.values():
        final_data.append({
            "Фамилия": user_data["Фамилия"],
            "Имя": user_data["Имя"],
            "Почта": user_data["Почта"],
            "Результат": user_data["Результат"],
            "Итог": user_data["Итог"],
            "Ответы": "\n\n".join(user_data["Ответы"])
        })

    if final_data:
        output_path = os.path.join(results_folder, "merged_report.xlsx")
        pd.DataFrame(final_data).to_excel(output_path, index=False)
        messagebox.showinfo("Готово", f"Отчёт сохранён:\n{output_path}")
    else:
        messagebox.showwarning("Пусто", "Нет данных для отчёта")


def browse_folder(entry):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry.delete(0, tk.END)
        entry.insert(0, folder_selected)

def browse_file(entry):
    file_selected = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file_selected:
        entry.delete(0, tk.END)
        entry.insert(0, file_selected)

def start_gui():
    root = tk.Tk()
    root.title("Сбор результатов тестирования SMLT")

    tk.Label(root, text="Папка с результатами (.csv):").grid(row=0, column=0, sticky="w")
    results_entry = tk.Entry(root, width=60)
    results_entry.grid(row=0, column=1)
    tk.Button(root, text="Обзор", command=lambda: browse_folder(results_entry)).grid(row=0, column=2)

    tk.Label(root, text="Файл с базой вопросов (.xlsx):").grid(row=1, column=0, sticky="w")
    questions_entry = tk.Entry(root, width=60)
    questions_entry.grid(row=1, column=1)
    tk.Button(root, text="Обзор", command=lambda: browse_file(questions_entry)).grid(row=1, column=2)

    tk.Button(root, text="Собрать отчёт", command=lambda: run_script(results_entry.get(), questions_entry.get()), bg="green", fg="white").grid(row=2, column=1, pady=10)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
