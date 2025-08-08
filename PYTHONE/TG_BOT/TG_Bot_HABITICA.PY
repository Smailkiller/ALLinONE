import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import calendar
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import json


# Загрузка данных из JSON
def load_data():
    try:
        with open('habits_data.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_data(data):
    with open('habits_data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# Обработчик команды /start
async def start(update: Update, context):
    # Кнопки для встроенной клавиатуры (Reply Keyboard)
    reply_keyboard = [
        ["ИНФО", "DEL"]
    ]

    await update.message.reply_text(
        "Выберите привычку или статистику:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)
    )

    # Инлайн-кнопки для выбора привычек и статистики
    keyboard = [
        [InlineKeyboardButton("💨", callback_data="habit_kalyan"),
         InlineKeyboardButton("🍻", callback_data="habit_alcohol"),
         InlineKeyboardButton("💪", callback_data="habit_strength")],
        [InlineKeyboardButton("Месяц", callback_data="stat_negative_month"),
         InlineKeyboardButton("Квартал", callback_data="stat_negative_quarter"),
         InlineKeyboardButton("Год", callback_data="stat_negative_year")],

        [InlineKeyboardButton("📚", callback_data="habit_manga"),
         InlineKeyboardButton("🎥", callback_data="habit_anime"),
         InlineKeyboardButton("🎮", callback_data="habit_games")],
        [InlineKeyboardButton("Месяц", callback_data="stat_entertainment_month"),
         InlineKeyboardButton("Квартал", callback_data="stat_entertainment_quarter"),
         InlineKeyboardButton("Год", callback_data="stat_entertainment_year")],

        [InlineKeyboardButton("🚿", callback_data="habit_spraying"),
         InlineKeyboardButton("💧", callback_data="habit_watering"),
         InlineKeyboardButton("🧺", callback_data="habit_replanting")],
        [InlineKeyboardButton("Месяц", callback_data="stat_plant_month"),
         InlineKeyboardButton("Квартал", callback_data="stat_plant_quarter"),
         InlineKeyboardButton("Год", callback_data="stat_plant_year")],

        [InlineKeyboardButton("🤧", callback_data="habit_sick"),
         InlineKeyboardButton("🚑", callback_data="habit_doctor"),
         InlineKeyboardButton("🛁", callback_data="habit_shower")],
        [InlineKeyboardButton("Месяц", callback_data="stat_health_month"),
         InlineKeyboardButton("Квартал", callback_data="stat_health_quarter"),
         InlineKeyboardButton("Год", callback_data="stat_health_year")]
    ]
    await update.message.reply_text("Выберите привычку или статистику:", reply_markup=InlineKeyboardMarkup(keyboard))


# Обработчик кнопки "ИНФО"
async def show_info(update: Update, context):
    data = load_data().get(str(update.effective_user.id), {})
    date_today = datetime.now().strftime("%Y-%m-%d")
    message = "Привычки за сегодня:\n"
    habits_today = False

    for habit, dates in data.items():
        if date_today in dates:
            message += f"• {habit}: {dates[date_today]} раз(а)\n"
            habits_today = True

    if not habits_today:
        message += "Сегодня записей нет."

    await update.message.reply_text(message)

# Обработчик кнопки "DEL"
async def clear_chat(update: Update, context):
    # Очищает переписку, отправляя начальное состояние клавиатуры
    await start(update, context)

# Обработчики для команд "ИНФО" и "DEL" из панели клавиатуры
async def handle_reply_keyboard(update: Update, context):
    text = update.message.text
    if text == "ИНФО":
        await show_info(update, context)
    elif text == "DEL":
        await clear_chat(update, context)

# Функция для записи привычки
async def log_habit(update: Update, context):
    data = load_data()
    habit = update.callback_query.data
    date_today = datetime.now().strftime("%Y-%m-%d")
    user_id = str(update.effective_user.id)

    if user_id not in data:
        data[user_id] = {}
    if habit not in data[user_id]:
        data[user_id][habit] = {}
    if date_today in data[user_id][habit]:
        data[user_id][habit][date_today] += 1
    else:
        data[user_id][habit][date_today] = 1

    save_data(data)
    await update.callback_query.answer(f"Привычка {habit} зафиксирована!")


# Функция для генерации тепловой карты
async def generate_heatmap(update, context, period, habits, color_map, title):
    data = load_data().get(str(update.effective_user.id), {})
    if not data:
        await update.callback_query.answer("У вас пока нет записанных привычек.")
        return

    try:
        now = datetime.now()

        if period == "month":
            days_in_period = calendar.monthrange(now.year, now.month)[1]
            start_date = datetime(now.year, now.month, 1)
            period_title = f"{title} ({now.strftime('%B')})"
        elif period == "quarter":
            start_month = (now.month - 1) // 3 * 3 + 1
            start_date = datetime(now.year, start_month, 1)
            days_in_period = 90
            period_title = f"{title} (Текущий квартал)"
        elif period == "year":
            start_date = datetime(now.year, 1, 1)
            days_in_period = 365
            period_title = f"{title} (Текущий год)"

        habit_counts = {habit: np.zeros(days_in_period) for habit in habits}

        for habit_key, dates in data.items():
            if habit_key in habits:
                for date_str, count in dates.items():
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if start_date <= date < start_date + timedelta(days=days_in_period):
                        day_index = (date - start_date).days
                        habit_counts[habit_key][day_index] = count

        heatmap_data = np.array(list(habit_counts.values()))

        fig, ax = plt.subplots(figsize=(12, 5))
        heatmap = ax.imshow(heatmap_data, cmap=color_map, aspect="auto", interpolation="nearest", vmin=0)

        ax.set_xticks(range(0, days_in_period, max(1, days_in_period // 30)))
        ax.set_xticklabels(range(1, days_in_period + 1, max(1, days_in_period // 30)), rotation=45)
        ax.set_yticks(range(len(habits)))
        ax.set_yticklabels(habits)
        ax.set_title(period_title)
        plt.colorbar(heatmap, label="Количество записей")

        for i, habit in enumerate(habits):
            for j in range(days_in_period):
                count = habit_counts[habit][j]
                if count > 0:
                    ax.text(j, i, int(count), ha="center", va="center", color="black")

        ax.grid(which="both", color="gray", linestyle="--", linewidth=0.5)
        ax.set_xticks(np.arange(-0.5, days_in_period, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(habits), 1), minor=True)
        ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)
        ax.tick_params(which="minor", size=0)

        plt.tight_layout()
        heatmap_path = "habit_heatmap.png"
        plt.savefig(heatmap_path)
        await update.callback_query.message.reply_photo(photo=open(heatmap_path, "rb"))
        os.remove(heatmap_path)

        await update.callback_query.answer("График отправлен!")

    except Exception as e:
        print(f"Ошибка при генерации тепловой карты: {e}")
        await update.callback_query.answer("Произошла ошибка при генерации графика.")


# Обработчики статистики для каждого списка и периода
async def stat_negative_month(update: Update, context):
    await generate_heatmap(update, context, "month", ["habit_kalyan", "habit_alcohol", "habit_strength"], "Reds",
                           "Негативные привычки")


async def stat_negative_quarter(update: Update, context):
    await generate_heatmap(update, context, "quarter", ["habit_kalyan", "habit_alcohol", "habit_strength"], "Reds",
                           "Негативные привычки")


async def stat_negative_year(update: Update, context):
    await generate_heatmap(update, context, "year", ["habit_kalyan", "habit_alcohol", "habit_strength"], "Reds",
                           "Негативные привычки")


async def stat_entertainment_month(update: Update, context):
    await generate_heatmap(update, context, "month", ["habit_manga", "habit_anime", "habit_games"], "Blues",
                           "Развлекательные привычки")


async def stat_entertainment_quarter(update: Update, context):
    await generate_heatmap(update, context, "quarter", ["habit_manga", "habit_anime", "habit_games"], "Blues",
                           "Развлекательные привычки")


async def stat_entertainment_year(update: Update, context):
    await generate_heatmap(update, context, "year", ["habit_manga", "habit_anime", "habit_games"], "Blues",
                           "Развлекательные привычки")


async def stat_plant_month(update: Update, context):
    await generate_heatmap(update, context, "month", ["habit_spraying", "habit_watering", "habit_replanting"], "Greens",
                           "Уход за растениями")


async def stat_plant_quarter(update: Update, context):
    await generate_heatmap(update, context, "quarter", ["habit_spraying", "habit_watering", "habit_replanting"],
                           "Greens", "Уход за растениями")


async def stat_plant_year(update: Update, context):
    await generate_heatmap(update, context, "year", ["habit_spraying", "habit_watering", "habit_replanting"], "Greens",
                           "Уход за растениями")


async def stat_health_month(update: Update, context):
    await generate_heatmap(update, context, "month", ["habit_sick", "habit_doctor", "habit_shower"], "Oranges",
                           "Здоровье")


async def stat_health_quarter(update: Update, context):
    await generate_heatmap(update, context, "quarter", ["habit_sick", "habit_doctor", "habit_shower"], "Oranges",
                           "Здоровье")


async def stat_health_year(update: Update, context):
    await generate_heatmap(update, context, "year", ["habit_sick", "habit_doctor", "habit_shower"], "Oranges",
                           "Здоровье")


# Основная функция для запуска бота
def main():
    application = Application.builder().token("TOKEN").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_keyboard))

    # Обработчики привычек
    habit_patterns = [
        "habit_kalyan", "habit_alcohol", "habit_strength",
        "habit_manga", "habit_anime", "habit_games",
        "habit_spraying", "habit_watering", "habit_replanting",
        "habit_sick", "habit_doctor", "habit_shower"
    ]
    for pattern in habit_patterns:
        application.add_handler(CallbackQueryHandler(log_habit, pattern=f"^{pattern}$"))

    # Обработчики статистики для каждого списка и периода
    application.add_handler(CallbackQueryHandler(stat_negative_month, pattern="^stat_negative_month$"))
    application.add_handler(CallbackQueryHandler(stat_negative_quarter, pattern="^stat_negative_quarter$"))
    application.add_handler(CallbackQueryHandler(stat_negative_year, pattern="^stat_negative_year$"))

    application.add_handler(CallbackQueryHandler(stat_entertainment_month, pattern="^stat_entertainment_month$"))
    application.add_handler(CallbackQueryHandler(stat_entertainment_quarter, pattern="^stat_entertainment_quarter$"))
    application.add_handler(CallbackQueryHandler(stat_entertainment_year, pattern="^stat_entertainment_year$"))

    application.add_handler(CallbackQueryHandler(stat_plant_month, pattern="^stat_plant_month$"))
    application.add_handler(CallbackQueryHandler(stat_plant_quarter, pattern="^stat_plant_quarter$"))
    application.add_handler(CallbackQueryHandler(stat_plant_year, pattern="^stat_plant_year$"))

    application.add_handler(CallbackQueryHandler(stat_health_month, pattern="^stat_health_month$"))
    application.add_handler(CallbackQueryHandler(stat_health_quarter, pattern="^stat_health_quarter$"))
    application.add_handler(CallbackQueryHandler(stat_health_year, pattern="^stat_health_year$"))

    application.run_polling()


if __name__ == '__main__':
    main()
