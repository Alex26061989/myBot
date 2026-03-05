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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("🚀 START"))
    markup.add(types.KeyboardButton("🔍 Поиск"))
    bot.send_message(
        chat_id,
        "👋 Привет!\n\nЯ помогу подобрать игрушку для ребёнка 🎁\n\nНажми START, чтобы начать 👇",
        reply_markup=markup
    )
@bot.message_handler(func=lambda message: message.text == "🔍 Поиск")
def search_button(message):
    search_command(message)    

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

# =================
# Поисковая команда    
# =================
@bot.message_handler(commands=["search"])
def search_command(message):
    chat_id = message.chat.id
    msg = bot.send_message(
        chat_id,
        "🔍 Введите слово или фразу для поиска (например: бизиборд, конструктор, кукла):"
    )
    bot.register_next_step_handler(msg, process_search)

def process_search(message):
    chat_id = message.chat.id
    query = message.text.lower().strip()
    
    if len(query) < 2:
        bot.send_message(chat_id, "Слишком короткий запрос. Введите хотя бы 2 буквы.")
        return
    
    # Ищем по названию и описанию
    results = []
    for toy in TOYS:
        # Поиск в названии
        if query in toy['name'].lower():
            results.append(toy)
            continue
        # Поиск в описании
        desc = str(toy['description']).lower()
        if query in desc:
            results.append(toy)
    
    if not results:
        bot.send_message(
            chat_id,
            f"😕 По запросу '{message.text}' ничего не найдено.\nПопробуйте другие слова."
        )
        return
    
    # Показываем результаты
    bot.send_message(chat_id, f"✅ Найдено товаров: {len(results)}")
    
    for toy in results[:5]:  # Показываем первые 5, чтобы не спамить
        add_view(toy["id"])
        text = f"🧸 <b>{toy['name']}</b>\n\n{toy['description']}\n\n💰 Цена: {toy['price']}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Купить", url=toy["link"]))
        
        if toy.get("image"):
            bot.send_photo(chat_id, toy["image"], caption=text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    
    if len(results) > 5:
        bot.send_message(
            chat_id,
            f"... и ещё {len(results) - 5} товаров. Уточните запрос для более точного поиска."
        )

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
            show_target_groups(chat_id)
            
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
