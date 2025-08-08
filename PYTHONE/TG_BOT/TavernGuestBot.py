import telebot
import os
import pandas as pd
import subprocess
import time

# --- Конфигурация ---
TOKEN = "TOKEN"
ADMIN_ID = 0000000
CHAT_ID = -111111111  # Чат, куда отправляем

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
EXCEL_FILE = "data_test.xlsx"
MEDIA_FOLDER = "media_files"

bot = telebot.TeleBot(TOKEN)

def convert_to_ogg(input_path: str, output_path: str):
    """Конвертация в .ogg (libopus) с настройками для Telegram voice"""
    if os.path.exists(output_path):
        os.remove(output_path)
    cmd = [
        FFMPEG_PATH,
        "-i", input_path,
        "-vn",              # убираем видео, если есть
        "-ac", "1",         # моно
        "-ar", "48000",     # частота дискретизации
        "-c:a", "libopus",  # кодек для Telegram
        "-application", "voip",  # важно для голосового
        "-b:a", "64k",
        "-f", "ogg",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path

@bot.message_handler(commands=["go"])
def handle_go(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Только админ может использовать эту команду.")
        return

    if not os.path.exists(EXCEL_FILE):
        bot.reply_to(message, "❌ Файл data_test.xlsx не найден.")
        return

    df = pd.read_excel(EXCEL_FILE)

    if "status" not in df.columns:
        df["status"] = ""

    df["status"] = df["status"].astype(str).fillna("")
    updated = False

    for idx, row in df.iterrows():
        if str(row.get("status")).strip().lower() == "sent":
            continue

        text = str(row.get("text")).strip() if pd.notna(row.get("text")) else ""
        media_file = str(row.get("media")).strip() if pd.notna(row.get("media")) else None

        if not media_file:
            bot.send_message(ADMIN_ID, f"⚠ Нет имени файла в строке {idx+2}")
            continue

        input_path = os.path.join(MEDIA_FOLDER, media_file)

        if not os.path.exists(input_path):
            bot.send_message(ADMIN_ID, f"❌ Файл не найден: {input_path}")
            continue

        # Если уже ogg — не конвертируем
        if media_file.lower().endswith(".ogg"):
            ogg_path = input_path
        else:
            ogg_path = input_path + ".ogg"
            convert_to_ogg(input_path, ogg_path)

        if not os.path.exists(ogg_path):
            bot.send_message(ADMIN_ID, f"❌ Ошибка: ogg файл не создан для {media_file}")
            continue

        # Небольшая пауза между отправками
        time.sleep(2)

        try:
            with open(ogg_path, "rb") as voice:
                bot.send_voice(CHAT_ID, voice, caption=text)
            df.at[idx, "status"] = "sent"
            updated = True
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Ошибка при отправке строки {idx+2}: {e}")

    if updated:
        df.to_excel(EXCEL_FILE, index=False)
        bot.send_message(ADMIN_ID, "✅ Все новые сообщения отправлены.")
    else:
        bot.send_message(ADMIN_ID, "ℹ️ Новых сообщений для отправки нет.")

bot.polling(none_stop=True)
