import telebot
import os
from telebot import types
from dotenv import load_dotenv

import config
from categories import TARGET_GROUPS, AGE_GROUPS, TOY_TYPES
from data import TOYS
from stats import add_view
from announcer import announce_new_toys

load_dotenv()  # загружает переменные из .env файла
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(config.TOKEN)

if __name__ == '__main__':
    # Сначала проверяем новые товары и отправляем анонсы
    try:
        announce_new_toys(bot)
    except Exception as e:
        print(f"Ошибка в модуле анонсов: {e}")
    
    # Затем запускаем бота
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)

# состояние пользователей
user_state = {}

# =========================
# /start + welcome
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    markup.add(types.KeyboardButton("🚀 START"))

    bot.send_message(
        chat_id,
        "👋 Привет!\n\n"
        "Я помогу подобрать игрушку для ребёнка 🎁\n\n"
        "Нажми START, чтобы начать 👇",
        reply_markup=markup
    )

# =========================
# START кнопка
# =========================
@bot.message_handler(func=lambda message: message.text == "🚀 START")
def start_by_button(message):
    chat_id = message.chat.id

    user_state[chat_id] = {}

    # убираем нижнюю клавиатуру
    remove_markup = types.ReplyKeyboardRemove()

    bot.send_message(
       chat_id,
       "👶 Для кого ищем игрушку?",
       reply_markup=remove_markup
    )

    show_target_groups(chat_id)

# =========================
# 1️⃣ Для кого
# =========================
def show_target_groups(chat_id):
    markup = types.InlineKeyboardMarkup()
    for code, name in TARGET_GROUPS.items():
        markup.add(
            types.InlineKeyboardButton(
                name,
                callback_data=f"gender:{code}"
            )
        )

    bot.send_message(
        chat_id,
        "👶 Для кого ищем игрушку?",
        reply_markup=markup
    )

# =========================
# 2️⃣ Возраст
# =========================
def show_age_groups(chat_id):
    markup = types.InlineKeyboardMarkup()
    for code, name in AGE_GROUPS.items():
        markup.add(
            types.InlineKeyboardButton(
                name,
                callback_data=f"age:{code}"
            )
        )

    bot.send_message(
        chat_id,
        "🎂 Возраст ребёнка:",
        reply_markup=markup
    )

# =========================
# 3️⃣ Тип игрушки
# =========================
def show_toy_types(chat_id):
    markup = types.InlineKeyboardMarkup()
    for code, name in TOY_TYPES.items():
        markup.add(
            types.InlineKeyboardButton(
                name,
                callback_data=f"type:{code}"
            )
        )

    bot.send_message(
        chat_id,
        "🧸 Что ищем?",
        reply_markup=markup
    )

# =========================
# CALLBACKS
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    import traceback
    chat_id = call.message.chat.id
    data = call.data
    
    print("="*50)
    print(f"🔥 ПОЛУЧЕН CALLBACK: {data}")
    print(f"   от пользователя: {chat_id}")
    print(f"   время: {__import__('datetime').datetime.now()}")
    print("="*50)
    
    try:
        if data == "restart":
            print(f"🔄 ОБРАБОТКА restart для {chat_id}")
            user_state[chat_id] = {}
            print(f"   состояние сброшено, вызываю show_target_groups")
            show_target_groups(chat_id)
            print(f"   функция show_target_groups вызвана")
            
        elif data.startswith("gender:"):
            gender = data.split(":")[1]
            print(f"👤 Выбрано gender: {gender}")
            user_state[chat_id]["gender"] = gender
            show_age_groups(chat_id)
            
        elif data.startswith("age:"):
            age = data.split(":")[1]
            print(f"🎂 Выбрано age: {age}")
            user_state[chat_id]["age"] = age
            show_toy_types(chat_id)
            
        elif data.startswith("type:"):
            toy_type = data.split(":")[1]
            print(f"🧸 Выбрано type: {toy_type}")
            user_state[chat_id]["type"] = toy_type
            show_results(chat_id)
            
        else:
            print(f"❓ Неизвестный callback: {data}")
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА:")
        print(f"   {str(e)}")
        print(f"   {traceback.format_exc()}")
        bot.send_message(chat_id, "Произошла ошибка. Напишите /start чтобы продолжить.")

# =========================
# РЕЗУЛЬТАТЫ
# =========================
def show_results(chat_id):
    state = user_state.get(chat_id, {})

    results = [
        toy for toy in TOYS
        if (
            state.get("age") in toy.get("age", [])
            and state.get("type") in toy.get("type", [])
            and (
                "all" in toy.get("gender", [])
                or state.get("gender") in toy.get("gender", [])
            )
        )
    ]

    if not results:
        bot.send_message(
            chat_id,
            "😕 Ничего не нашли, попробуй ещё раз."
        )
        show_target_groups(chat_id)
        return

    for toy in results:
        add_view(toy["id"])

        text = (
            f"🧸 <b>{toy['name']}</b>\n\n"
            f"{toy['description']}\n\n"
            f"💰 Цена: {toy['price']}"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🛒 Купить",
                url=toy["link"]
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "🔁 Начать заново",
                callback_data="restart"
            )
        )

        if toy.get("image"):
            bot.send_photo(
                chat_id,
                toy["image"],
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                chat_id,
                text,
                reply_markup=markup,
                parse_mode="HTML"
            )


# =========================
# ЗАПУСК
# =========================
# print("🚀 Бот запущен")
# bot.infinity_polling()
