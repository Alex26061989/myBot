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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================
def return_to_menu(chat_id):
    """Возвращает пользователя в главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📋 Поиск по каталогу")
    btn2 = types.KeyboardButton("🔍 Поиск по слову")
    markup.add(btn1, btn2)
    
    bot.send_message(
        chat_id,
        "🏠 Главное меню. Выберите способ поиска:",
        reply_markup=markup
    )

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

# =========================
# Функция для показа одного товара
# =========================
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
# ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ
# =========================
@bot.message_handler(func=lambda message: message.text == "📋 Поиск по каталогу")
def catalog_search(message):
    chat_id = message.chat.id
    user_state[chat_id] = {}
    
    # Убираем клавиатуру с кнопками
    remove_markup = types.ReplyKeyboardRemove()
    bot.send_message(
        chat_id,
        "👶 Для кого ищем игрушку?",
        reply_markup=remove_markup
    )
    
    show_target_groups(chat_id)


@bot.message_handler(func=lambda message: message.text == "🔍 Поиск по слову")
def word_search(message):
    chat_id = message.chat.id
    
    # Убираем клавиатуру с кнопками
    remove_markup = types.ReplyKeyboardRemove()
    
    msg = bot.send_message(
        chat_id,
        "🔍 Введите слово или фразу для поиска\n"
        "(например: бизиборд, конструктор, кукла, машина, доктор):",
        reply_markup=remove_markup
    )
    bot.register_next_step_handler(msg, process_word_search)


def process_word_search(message):
    chat_id = message.chat.id
    query = message.text.lower().strip()
    
    if len(query) < 2:
        bot.send_message(chat_id, "⚠️ Слишком короткий запрос. Введите хотя бы 2 буквы.")
        return_to_menu(chat_id)
        return
    
    # Ищем по названию и описанию
    results = []
    for toy in TOYS:
        # Поиск в названии
        if query in toy['name'].lower():
            results.append(toy)
            continue
        # Поиск в описании (преобразуем в строку)
        desc = str(toy['description']).lower()
        if query in desc:
            results.append(toy)
    
    if not results:
        bot.send_message(
            chat_id,
            f"😕 По запросу '{message.text}' ничего не найдено.\nПопробуйте другие слова."
        )
        return_to_menu(chat_id)
        return
    
    # Показываем результаты
    bot.send_message(
        chat_id,
        f"✅ Найдено товаров: {len(results)}. Показываю первые 5:"
    )
    
    # Показываем первые 5 результатов
    for toy in results[:5]:
        add_view(toy["id"])
        
        # Берём первые 150 символов описания
        desc = str(toy['description'])
        if len(desc) > 150:
            desc = desc[:150] + "..."
        
        text = (
            f"🧸 <b>{toy['name']}</b>\n\n"
            f"{desc}\n\n"
            f"💰 Цена: {toy['price']}"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Купить", url=toy["link"]))
        
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
    
    if len(results) > 5:
        bot.send_message(
            chat_id,
            f"... и ещё {len(results) - 5} товаров. Уточните запрос для более точного поиска."
        )
    
    # Возвращаем в меню
    return_to_menu(chat_id)

# =========================
# Тестовая команда
# =========================
@bot.message_handler(commands=["test"])
def test_command(message):
    print(f"✅ ТЕСТОВАЯ КОМАНДА от {message.chat.id}")
    bot.reply_to(message, "Бот работает! 🎉")

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
        return_to_menu(chat_id)  # Возвращаем в меню
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
    
    # После показа результатов возвращаем в меню
    return_to_menu(chat_id)

# =========================
# ЗАПУСК (В САМОМ КОНЦЕ!)
# =========================
if __name__ == '__main__':
    try:
        announce_new_toys(bot)
    except Exception as e:
        print(f"Ошибка в модуле анонсов: {e}")
    
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
    