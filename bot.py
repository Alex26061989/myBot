import telebot
import os
from telebot import types
from dotenv import load_dotenv

import config
from categories import TARGET_GROUPS, AGE_GROUPS, TOY_TYPES
from data import TOYS
from stats import add_view
from announcer import announce_new_toys

print("🔥🔥🔥 БОТ ЗАПУСКАЕТСЯ НА RAILWAY")
print(f"Токен: {config.TOKEN[:10]}... (скрыто)")
print(f"Время: {__import__('datetime').datetime.now()}")

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(config.TOKEN)

# состояние пользователей
user_state = {}

# =========================
# /start + welcome
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    args = message.text.split()
    
    # Проверяем, есть ли параметр (например, /start toy_47)
    if len(args) > 1 and args[1].startswith("toy_"):
        try:
            toy_id = int(args[1].replace("toy_", ""))
            toy = next((t for t in TOYS if t['id'] == toy_id), None)
            if toy:
                show_single_toy(chat_id, toy)
                return
        except:
            pass
    
    # Сбрасываем состояние пользователя
    user_state[chat_id] = {}
    
    # Создаём красивое меню с двумя кнопками
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📋 Поиск по каталогу")
    btn2 = types.KeyboardButton("🔍 Поиск по слову")
    markup.add(btn1, btn2)
    
    bot.send_message(
        chat_id,
        "👋 Привет! Я помогу подобрать игрушку для ребёнка 🎁\n\nВыбери способ поиска:",
        reply_markup=markup
    )    

# Новая функция для показа одного товара
def show_single_toy(chat_id, toy):
    add_view(toy["id"])
    text = f"🧸 <b>{toy['name']}</b>\n\n{toy['description']}\n\n💰 Цена: {toy['price']}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 Купить", url=toy["link"]))
    markup.add(types.InlineKeyboardButton("🔁 Начать заново", callback_data="restart"))
    
    if toy.get("image"):
        bot.send_photo(chat_id, toy["image"], caption=text, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML") 

    

# =========================
# Тестовая команда
# =========================
@bot.message_handler(commands=["test"])
def test_command(message):
    print(f"✅ ТЕСТОВАЯ КОМАНДА от {message.chat.id}")
    bot.reply_to(message, "Бот работает! 🎉")

# =========================
# START кнопка
# =========================
@bot.message_handler(func=lambda message: message.text == "🚀 START")
def start_by_button(message):
    chat_id = message.chat.id
    user_state[chat_id] = {}
    remove_markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "👶 Для кого ищем игрушку?", reply_markup=remove_markup)
    show_target_groups(chat_id)

# =========================
# 1️⃣ Для кого
# =========================
def show_target_groups(chat_id):
    markup = types.InlineKeyboardMarkup()
    for code, name in TARGET_GROUPS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"gender:{code}"))
    bot.send_message(chat_id, "👶 Для кого ищем игрушку?", reply_markup=markup)

# =========================
# 2️⃣ Возраст
# =========================
def show_age_groups(chat_id):
    markup = types.InlineKeyboardMarkup()
    for code, name in AGE_GROUPS.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"age:{code}"))
    bot.send_message(chat_id, "🎂 Возраст ребёнка:", reply_markup=markup)

# =========================
# 3️⃣ Тип игрушки
# =========================
def show_toy_types(chat_id):
    markup = types.InlineKeyboardMarkup()
    for code, name in TOY_TYPES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"type:{code}"))
    bot.send_message(chat_id, "🧸 Что ищем?", reply_markup=markup)

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
            return_to_menu(chat_id)  # Возвращаем в меню
            
        elif data.startswith("gender:"):
            gender = data.split(":")[1]
            user_state[chat_id]["gender"] = gender
            show_age_groups(chat_id)
            
        elif data.startswith("age:"):
            age = data.split(":")[1]
            user_state[chat_id]["age"] = age
            show_toy_types(chat_id)
            
        elif data.startswith("type:"):
            toy_type = data.split(":")[1]
            user_state[chat_id]["type"] = toy_type
            show_results(chat_id)
            
        else:
            print(f"❓ Неизвестный callback: {data}")
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print(traceback.format_exc())
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
        bot.send_message(chat_id, "😕 Ничего не нашли, попробуй ещё раз.")
        show_target_groups(chat_id)
        return

    for toy in results:
        add_view(toy["id"])
        text = f"🧸 <b>{toy['name']}</b>\n\n{toy['description']}\n\n💰 Цена: {toy['price']}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Купить", url=toy["link"]))
        markup.add(types.InlineKeyboardButton("🔁 Начать заново", callback_data="restart"))

        if toy.get("image"):
            bot.send_photo(chat_id, toy["image"], caption=text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

# =========================
# ЗАПУСК (ТЕПЕРЬ В САМОМ КОНЦЕ!)
# =========================
if __name__ == '__main__':
    try:
        announce_new_toys(bot)
    except Exception as e:
        print(f"Ошибка в модуле анонсов: {e}")
    
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
