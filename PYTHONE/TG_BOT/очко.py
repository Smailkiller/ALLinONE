import os
import telebot
import json
import requests
import time
import threading
from random import choice
from datetime import datetime, timedelta
from telebot.types import Message
import pandas as pd
import logging

# Конфигурация
TOKEN = "TOKEN" 
ADMIN_ID = 0000
GROUP_ID = -11111
BOT_TOKEN = os.getenv("BOT_TOKEN", "TOKEN")
EXCEL_FILE = "data.xlsx"
MEDIA_FOLDER = "media_files"
AUTH_LOG = "auth_failures.log"
ERROR_LOG = "errors.log"

# Логирование
logging.basicConfig(level=logging.INFO)
if not os.path.exists(AUTH_LOG):
    open(AUTH_LOG, "w").close()
if not os.path.exists(ERROR_LOG):
    open(ERROR_LOG, "w").close()

auth_logger = logging.getLogger("auth_failures")
error_logger = logging.getLogger("errors")

bot = telebot.TeleBot(TOKEN)

# Путь к JSON-файлам
boys_file_path = "boys_library.json"
girls_file_path = "girls_library.json"
respect_file_path = "respect_library.json"


# Проверка и создание файлов с пустыми данными, если они отсутствуют
def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        try:
            with open(file_path, "w") as file:
                json.dump({}, file)
            print(f"Файл {file_path} был успешно создан.")
        except Exception as e:
            print(f"Не удалось создать файл {file_path}: {e}")


ensure_file_exists(boys_file_path)
ensure_file_exists(girls_file_path)
ensure_file_exists(respect_file_path)

# Загрузка баз данных
with open(boys_file_path, "r") as boys_file, open(girls_file_path, "r") as girls_file, open(respect_file_path,
                                                                                            "r") as respect_file:
    boys_library = json.load(boys_file)
    girls_library = json.load(girls_file)
    respect_library = json.load(respect_file)

# Лимиты и авторизованные пользователи
authorized_girls = [
    "user1", "user2"]

authorized_boys = [
   "user3", "user4"]

# Словарь для хранения состояния пользователей
user_transaction_status = {}

def add_temp_limits(user_id, limit):
    """Добавляет временные лимиты пользователю."""
    # Инициализируем структуру данных для хранения лимитов, если её нет
    if user_id not in user_limits:
        user_limits[user_id] = {"temporary_limit": 0}

    # Увеличиваем временные лимиты
    user_limits[user_id]["temporary_limit"] += limit

def reset_transaction_timer(user_id):
    """Сбрасывает таймер для пользователя"""
    if user_id in user_transaction_status:
        user_transaction_status[user_id]['is_active'] = False


@bot.callback_query_handler(func=lambda call: call.data == "donate_complete")
def handle_donate_callback(call):
    """Обработчик нажатий кнопок"""
    user_id = call.from_user.id
    username = call.from_user.username or "Без имени"

    # Проверка, активен ли таймер
    if user_id in user_transaction_status and user_transaction_status[user_id]['is_active']:
        bot.send_message(call.message.chat.id, "Ваша транзакция уже в процессе проверки. Пожалуйста, подождите.")
        return

    # Установка состояния транзакции
    user_transaction_status[user_id] = {'is_active': True}

    # Уведомление для администратора
    bot.send_message(
        ADMIN_ID,
        f"Пользователь {username} с ID {user_id} пополнил баланс"
    )

    # Отправка ответного сообщения пользователю
    bot.send_message(user_id, "Ваша транзакция проверяется нашими маленькими помощниками, подождите.")

    # Запуск таймера на 5 минут
    timer_thread = threading.Timer(300, reset_transaction_timer, args=[user_id])
    timer_thread.start()




# Лимиты по начислению баллов
user_limits = {}
constant_limit = 2  # постоянный лимит в час
temporary_limit = 0  # временный лимит по умолчанию
max_points = 10  # максимальное количество баллов за раз
special_limit_users = ["user0003", "user0004"]


# Функция для отправки реакции
def send_react(token, chat_id, message_id, emoji):
    url = f'https://api.telegram.org/bot{token}/setMessageReaction'
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reaction': [{'type': 'emoji', 'emoji': emoji}],  # Передача реакции как объекта с эмодзи
        'is_big': False
    }
    requests.post(url, json=data)


user_limits = {}  # Словарь для хранения лимитов пользователей


def check_limits(user_id, points):
    """Проверка и использование лимитов пользователя на начисление баллов"""
    current_time = datetime.now()

    # Инициализация лимитов пользователя, если их нет
    if user_id not in user_limits:
        user_limits[user_id] = {
            "count": 0,
            "last_time": current_time,
            "temporary_limit": 0
        }

    limit_data = user_limits[user_id]

    # Сброс лимитов, если прошёл час с последнего начисления
    if 'last_time' not in limit_data:
        limit_data['last_time'] = current_time  # Инициализируем, если отсутствует

    if limit_data['last_time'] + timedelta(hours=1) < current_time:
        limit_data['count'] = 0
        limit_data['last_time'] = current_time

    # Вычисляем доступное количество баллов
    available_points = (2 * 10) + limit_data['temporary_limit']  # 2 стандартных попытки по 10 баллов

    # Проверяем, можно ли начислить запрашиваемое количество баллов
    if points <= available_points:
        # Используем временные лимиты, если они есть
        if limit_data['temporary_limit'] > 0 and points > (limit_data['temporary_limit'] * 10):
            # Если запрашиваемое количество баллов превышает временные лимиты, используем стандартные
            limit_data['count'] += points // 10  # Увеличиваем счётчик постоянных лимитов
        else:
            # Уменьшаем временный лимит на количество попыток
            limit_data['temporary_limit'] -= points // 10

        return True
    else:
        return False  # Нет доступных лимитов

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return response.json()

def send_media(chat_id, media_path, caption=None, media_type="photo"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/send{media_type.capitalize()}"
    if not os.path.exists(media_path):
        error_logger.error(f"Media file not found: {media_path}")
        return None

    files = {media_type: open(media_path, "rb")}
    payload = {"chat_id": chat_id}
    if caption:
        payload["caption"] = caption
    response = requests.post(url, data=payload, files=files)
    return response.json()

# Обработка команды /sendmail
@bot.message_handler(commands=["sendmail"])
def handle_sendmail(message: Message):
    if message.chat.type != "private" or message.from_user.id != ADMIN_ID:
        auth_logger.warning(f"Unauthorized access attempt from user ID: {message.from_user.id}")
        return

    bot.reply_to(message, "Отправка начата.")
    try:
        data = pd.read_excel(EXCEL_FILE)
        for index, row in data.iterrows():
            if row.get("status") == "sent":
                continue

            chat_id = row["chat_id"]
            text = row.get("text")
            media_file = row.get("media")
            status = "failed"

            try:
                if pd.notna(media_file):
                    media_path = os.path.join(MEDIA_FOLDER, media_file)
                    response = send_media(chat_id, media_path, caption=text)
                elif pd.notna(text):
                    response = send_message(chat_id, text)
                else:
                    continue

                if response and response.get("ok"):
                    status = "sent"
            except Exception as e:
                error_logger.error(f"Failed to send to {chat_id}: {str(e)}")

            data.at[index, "status"] = status

        data.to_excel(EXCEL_FILE, index=False)
    except Exception as e:
        error_logger.error(f"Error during sending: {str(e)}")

    bot.reply_to(message, "Отправка завершена.")

@bot.message_handler(commands=['send'])
def handle_send(message):
    """Команда для отправки сообщения пользователю по ID"""
    try:
        # Парсим команду: /send id text
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 3:
            bot.send_message(message.chat.id, "Используйте: /send [user_id] [текст]")
            return

        user_id = int(command_parts[1])  # Получаем ID пользователя
        text = command_parts[2]  # Получаем текст сообщения

        # Отправляем сообщение пользователю
        bot.send_message(user_id, text)

        # Уведомляем администратора об успешной отправке
        bot.send_message(message.chat.id, f"Сообщение успешно отправлено пользователю с ID {user_id}.")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: пользовательский ID должен быть числом.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

# Обработчик команды /ap
@bot.message_handler(commands=['ap'])
def handle_ap(message):
    """Обработка команды начисления баллов"""
    if message.reply_to_message:
        try:
            # Получаем количество баллов из команды
            points = int(message.text.split()[1])  # Предполагаем, что формат: /ap [баллы]
        except (IndexError, ValueError):
            send_react(TOKEN, message.chat.id, message.message_id, '🖕')
            return

        # Проверка, можно ли начислить запрашиваемые баллы
        if check_limits(message.from_user.id, points):  # Обновленная проверка лимитов
            sender = message.from_user.username
            receiver = message.reply_to_message.from_user.username

            # Начисление баллов в зависимости от групп
            if sender in authorized_girls and receiver in authorized_boys:
                update_rating("boys", receiver, points)
            elif sender in authorized_boys and receiver in authorized_girls:
                update_rating("girls", receiver, points)
            elif sender in authorized_boys and receiver in authorized_boys:
                update_rating("respect", receiver, points)
            elif sender in authorized_girls and receiver in authorized_girls:
                update_rating("respect", receiver, points)

            # Отправляем реакцию об успешном начислении
            send_react(TOKEN, message.chat.id, message.message_id, '✍')
        else:
            # Если лимиты исчерпаны, отправляем реакцию об ошибке
            send_react(TOKEN, message.chat.id, message.message_id, '🖕')
    else:
        send_react(TOKEN, message.chat.id, message.message_id, '🖕')


# Команда /r для вывода рейтингов
@bot.message_handler(commands=['r'])
def handle_rating(message):
    """Команда вывода рейтингов"""
    boys_rating = format_rating(boys_library)
    girls_rating = format_rating(girls_library)
    respect_rating = format_rating(respect_library)

    send_react(TOKEN, message.chat.id, message.message_id, '💯')
    bot.send_message(message.chat.id,
                     f"Рейтинг Мамырей:\n{boys_rating}\n________\nРейтинг Колтуш:\n{girls_rating}\n________\nРейтинг Респекта:\n{respect_rating}")


# Команда /ebal для конвертации баллов из Респекта
@bot.message_handler(commands=['ebal'])
def handle_ebal(message):
    """Конвертация баллов из Респекта"""
    user = message.from_user.username
    if user in respect_library:
        respect_points = respect_library[user]
        converted_points = int(respect_points * 0.7)
        bonus_points = int((respect_points - converted_points) * 0.1)

        respect_library[user] = 0
        if user in authorized_boys:
            update_rating("boys", user, converted_points)
        elif user in authorized_girls:
            update_rating("girls", user, converted_points)

        update_rating("respect", "user00", bonus_points)

        send_react(TOKEN, message.chat.id, message.message_id, '🦄')
        bot.send_message(message.chat.id,
                         f"{user} сделал конвертацию баллов, часть пропала, часть забрали Татары и отдали ЮЗЕРУ.")
    else:
        send_react(TOKEN, message.chat.id, message.message_id, '🖕')


# Обработка донатов
@bot.message_handler(commands=['donat'])
def handle_donat(message):
    """Команда доната с проверкой возможности отправки личных сообщений"""
    if message.chat.id in [-1111111, -11112] or message.chat.type == 'private':
        try:
            # Создаём кнопки для личного сообщения
            markup = telebot.types.InlineKeyboardMarkup()
            btn1 = telebot.types.InlineKeyboardButton("Я пополнил", callback_data="donate_complete")
            btn2 = telebot.types.InlineKeyboardButton("Отмена", callback_data="donate_cancel")
            markup.add(btn1, btn2)

            # Пытаемся отправить сообщение в личные сообщения пользователю
            bot.send_message(
                message.from_user.id,
                "Для временного расширения числа лимитов на начисление - пополните казну. 1 лимит - 10 рублей: https://www.tbank.ru/cf/ключи новый",
                reply_markup=markup  # Отправляем сообщение с кнопками
            )
            # Успешное отправление, ставим реакцию с кубком
            send_react(TOKEN, message.chat.id, message.message_id, '🏆')
        except Exception as e:
            # Если бот не может отправить сообщение (например, пользователь не начал чат с ботом)
            bot.send_message(message.chat.id, "Я не могу с тобой связаться, поэтому напиши мне первым в ЛС и потом закниь повторно команду.")
    else:
        bot.send_message(message.chat.id, "Эта команда может быть вызвана только из определённых чатов.")


@bot.callback_query_handler(func=lambda call: call.data in ["donate_complete", "donate_cancel"])
def handle_donate_callback(call):
    """Обработчик нажатий кнопок"""
    if call.data == "donate_complete":
        user_id = call.from_user.id
        username = call.from_user.username or "Без имени"
        bot.send_message(
            ADMIN_ID,
            f"Пользователь {username} с ID {user_id} пополнил баланс. Команды /donat_x {user_id} или /donat_ap {user_id} число"
        )
    elif call.data == "donate_cancel":
        bot.delete_message(call.message.chat.id, call.message.message_id)


# Обработчик команды /donat_ap для администрирования лимитов
@bot.message_handler(commands=['donat_ap'])
def handle_donat_ap(message):
    """Команда для администраторов для начисления временных лимитов"""
    if message.from_user.id == ADMIN_ID:
        try:
            # Парсинг команды: /donat_ap user_id limit
            command_parts = message.text.split()
            user_id = int(command_parts[1])  # Получаем ID пользователя
            limit = int(command_parts[2])  # Получаем число временных лимитов

            # Добавляем временные лимиты для пользователя
            add_temp_limits(user_id, limit)

            # Уведомляем администратора об успешном начислении
            bot.send_message(message.chat.id, f"Пользователю с ID {user_id} начислено {limit} временных лимитов.")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Используйте: /donat_ap [user_id] [число лимитов]")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

# Обработчик команды /donat_x для отправки сообщения с видео
@bot.message_handler(commands=['donat_x'])
def handle_donat_x(message):
    """Команда для отправки сообщения пользователю с видео"""
    if message.from_user.id == ADMIN_ID:
        try:
            command_parts = message.text.split()
            user_id = int(command_parts[1])  # Получаем ID пользователя

            bot.send_message(user_id, "Эй, ты че: https://vk.com/video-40023088_456244369")
            bot.send_message(message.chat.id, f"Сообщение отправлено пользователю с ID {user_id}.")

            # Сбрасываем таймер для текущего пользователя, если это необходимо
            reset_transaction_timer(user_id)
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Используйте: /donat_x [user_id]")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

# Обработчик команды /help для помощи
@bot.message_handler(commands=['help'])
def handle_help(message):
    """Команда помощи"""
    bot.send_message(message.chat.id, (
        "/ap - ответь на сообщение введи команду и баллы\n"
        "Либо ответом на сообщение с командой /ap баллы (и любой текст), либо /ap @пользователь баллы и текст.\n"
        "Баллы начислять можно 2 раза в час (или больше через донат), не больше 10.\n"
        "/r - выводит рейтинг\n"
        "/ebal - конвертировать 70% баллов Респекта в свой личный рейтинг, а 10% от остатка пойдут Карине.\n\n"
        "/donat - увеличить временно число лимитов за 💲💲💲\n\n"
        "Список реакций:\n"
        "✍ — успешное начисление баллов.\n"
        "🖕 — ошибка начисления или превышен лимит.\n"
        "💯 — при выводе рейтинга.\n"
        "🦄 — при конвертации баллов."
    ))


@bot.message_handler(commands=['sudo'])
def handle_sudo(message):
    """Команда для отображения лимитов пользователя по его ID"""
    try:
        # Получаем ID пользователя из команды
        user_id = int(message.text.split()[1])

        # Проверяем, есть ли пользователь в базе лимитов
        if user_id in user_limits:
            limit_data = user_limits[user_id]
            constant_limit = limit_data.get('count', 0)  # Постоянный лимит начислений
            temp_limit = limit_data.get('temporary_limit', 0)  # Временный лимит

            # Вывод лимитов пользователя
            bot.send_message(
                message.chat.id,
                f"Лимиты пользователя с ID {user_id}:\n"
                f"Постоянные начисления за час: {constant_limit}\n"
                f"Временные начисления за час: {temp_limit}\n"
                f"Общий лимит начислений в час: {constant_limit + temp_limit}"
            )
        else:
            bot.send_message(message.chat.id, f"Пользователь с ID {user_id} не найден в базе лимитов.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Ошибка: Используйте формат команды /sudo [user_id].")


# Функция обновления рейтинга
def update_rating(group, username, points):
    """Функция для обновления рейтинга"""
    if group == "boys":
        if username not in boys_library:
            boys_library[username] = 0
        boys_library[username] += points
        with open(boys_file_path, "w") as boys_file:
            json.dump(boys_library, boys_file)
    elif group == "girls":
        if username not in girls_library:
            girls_library[username] = 0
        girls_library[username] += points
        with open(girls_file_path, "w") as girls_file:
            json.dump(girls_library, girls_file)
    elif group == "respect":
        if username not in respect_library:
            respect_library[username] = 0
        respect_library[username] += points
        with open(respect_file_path, "w") as respect_file:
            json.dump(respect_library, respect_file)

# Форматирование рейтинга
def format_rating(library):
    """Форматирование рейтинга для вывода с сортировкой"""
    # Сортируем пользователей по баллам в порядке убывания
    sorted_users = sorted(library.items(), key=lambda item: item[1], reverse=True)
    return "\n".join([f"{user} - {points}" for user, points in sorted_users])

# Список эмоций, которые может использовать бот
emojis = ['👍', '👎', '❤', '🔥', '🤯', '😱','🤮', '👀']

@bot.message_handler(content_types=['text'])
def text_handler(message):
    """Обработчик текстовых сообщений"""
    # Генерация случайного числа от 1 до 100
    if choice(range(1, 101)) <= 5:  # Вероятность 5%
        emoji = choice(emojis)  # Случайный выбор эмоции
        # Отправка реакции на сообщение
        send_react(TOKEN, message.chat.id, message.message_id, emoji)

# Запуск бота
bot.polling(none_stop=True)
