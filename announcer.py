# announcer.py
import time
import json
import os
from datetime import datetime
import telebot
from data import TOYS
from categories import TOY_TYPES

# Настройки
CHANNEL_ID = '@KidsWorldInfo' 
LOG_FILE = os.path.join(os.path.dirname(__file__), 'sent_announcements.json')

# Используем Railway Volume для постоянного хранения
VOLUME_PATH = '/app/data'  # путь, который мы указали в Volume
if os.path.exists(VOLUME_PATH):
    LOG_FILE = os.path.join(VOLUME_PATH, 'sent_announcements.json')
    print(f"✅ Использую Volume: {LOG_FILE}")
else:
    # Для локальной разработки
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'sent_announcements.json')
    print(f"⚠️ Volume не найден, использую локальный файл: {LOG_FILE}")

# Проверяем, можем ли писать в Volume
def check_volume_access():
    try:
        # Создаём директорию, если её нет
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        # Пробуем записать тестовый файл
        test_file = os.path.join(os.path.dirname(LOG_FILE), 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"✅ Есть доступ к записи в: {os.path.dirname(LOG_FILE)}")
        return True
    except Exception as e:
        print(f"❌ НЕТ ДОСТУПА К ЗАПИСИ: {e}")
        return False

# Вызываем проверку
check_volume_access()

def load_sent_items():
    """Загружает список ID уже анонсированных товаров"""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('sent_ids', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_sent_items(sent_ids):
    """Сохраняет список анонсированных товаров"""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'last_update': datetime.now().isoformat(),
            'sent_ids': sent_ids
        }, f, ensure_ascii=False, indent=2)

def format_price(price):
    """Форматирует цену для красивого отображения"""
    # Убираем "от " если есть, но оставляем для понимания
    return price.replace('от ', 'от ').replace('руб', '₽')

def create_announcement_message(toy):
    """Создает красивое сообщение для канала с защитой от любых ошибок"""
    
    print(f"🔧 Создаю сообщение для товара ID {toy['id']}")
    
    try:
        # ===== БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ОПИСАНИЯ =====
        desc_text = ""
        try:
            if 'description' not in toy:
                desc_text = "Описание отсутствует"
                print("⚠️ Поле description отсутствует")
            elif isinstance(toy['description'], dict):
                # Если словарь - берём значения
                values = list(toy['description'].values())
                desc_text = ' '.join([str(v) for v in values if v])
                print(f"📝 Описание из словаря, значений: {len(values)}")
            elif isinstance(toy['description'], list):
                # Если список - объединяем
                desc_text = ' '.join([str(item) for item in toy['description'] if item])
                print(f"📝 Описание из списка, элементов: {len(toy['description'])}")
            elif isinstance(toy['description'], str):
                # Если строка - используем как есть
                desc_text = toy['description']
                print(f"📝 Описание из строки, длина: {len(desc_text)}")
            else:
                # Если что-то другое - преобразуем в строку
                desc_text = str(toy['description'])
                print(f"📝 Описание из {type(toy['description'])}")
        except Exception as e:
            print(f"⚠️ Ошибка при извлечении описания: {e}")
            desc_text = "Описание временно недоступно"
        
        # Обрезаем до 200 символов
        if len(desc_text) > 200:
            short_desc = desc_text[:200] + "..."
        else:
            short_desc = desc_text
        
        # ===== БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ИНФОРМАЦИИ =====
        # Название
        name = str(toy.get('name', 'Без названия'))
        
        # Цена
        price = str(toy.get('price', 'Цена не указана'))
        price = price.replace('от ', 'от ').replace('руб', '₽')
        
        # Возраст
        age_list = toy.get('age', [])
        if isinstance(age_list, list):
            age_str = ', '.join([str(a) for a in age_list])
        else:
            age_str = str(age_list)
        
        # Типы
        type_list = toy.get('type', [])
        if isinstance(type_list, list):
            type_str = ', '.join([str(t) for t in type_list])
        else:
            type_str = str(type_list)
        
        # Иконка возраста
        if "0-1" in age_str:
            age_icon = "👶"
        elif "1-3" in age_str:
            age_icon = "🧒"
        else:
            age_icon = "👦"
        
        # ===== ФОРМИРУЕМ СООБЩЕНИЕ =====
        message = f"<b>🆕 НОВИНКА В НАШЕМ КАТАЛОГЕ!</b>\n\n"
        message += f"<b>{name}</b>\n\n"
        message += f"<i>{short_desc}</i>\n\n"
        message += f"💰 <b>Цена:</b> {price}\n"
        message += f"{age_icon} <b>Возраст:</b> {age_str} лет\n"
        message += f"🎁 <b>Категория:</b> {type_str}\n\n"
        
        # Ссылка на бота с конкретным товаром
        toy_link = f"https://t.me/ToyChoiseBot?start=toy_{toy['id']}"
        message += f"👇 <b>Забрать игрушку можно в нашем боте:</b>\n"
        message += f"👉 <a href='{toy_link}'>Перейти к товару</a>\n\n"
        
        # Хэштеги
        hashtags = []
        if isinstance(type_list, list):
            for t in type_list[:3]:  # первые 3 типа
                hashtags.append(f"#{t}")
        if age_list and len(age_list) > 0:
            hashtags.append(f"#{age_list[0]}")
        message += " ".join(hashtags)
        
        print(f"✅ Сообщение создано успешно для ID {toy['id']}")
        return message
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в create_announcement_message: {e}")
        import traceback
        traceback.print_exc()
        
        # Возвращаем минимальное сообщение в случае ошибки
        return f"<b>🆕 НОВИНКА!</b>\n\n{toy.get('name', 'Товар')}\n\n👉 https://t.me/ToyChoiseBot?start=toy_{toy['id']}"

def announce_new_toys(bot):
    """Основная функция для анонсирования новых товаров с защитой от лимитов"""
    
    print("🔄 Проверяем новые товары для анонса...")
    
    # Загружаем список уже анонсированных
    sent_ids = load_sent_items()
    
    # Получаем ID всех текущих товаров
    current_ids = [toy['id'] for toy in TOYS]
    
    # Находим новые товары (которых нет в sent_ids)
    new_ids = [tid for tid in current_ids if tid not in sent_ids]
    
    if not new_ids:
        print("✅ Новых товаров нет")
        return
    
    print(f"🎉 Найдено новых товаров: {len(new_ids)}")
    
    # Счетчик для контроля скорости
    sent_count = 0
    
    # Отправляем анонсы для каждого нового товара
    for index, toy_id in enumerate(new_ids):
        # Находим товар по ID
        toy = next((t for t in TOYS if t['id'] == toy_id), None)
        if not toy:
            continue
        
        try:
            # Создаем сообщение
            message = create_announcement_message(toy)

            # Отладка
            print(f"🔧 Создаю сообщение для товара ID {toy['id']}")
            print(f"   Тип description: {type(toy['description'])}")
            
            # Отправляем в канал
            if toy.get('image'):
                try:
                    bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=toy['image'],
                        caption=message,
                        parse_mode='HTML'
                    )
                except Exception as photo_error:
                    # Если фото не грузится - шлем без фото
                    print(f"⚠️ Ошибка с фото, шлем без фото: {photo_error}")
                    bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=message,
                        parse_mode='HTML'
                    )
            else:
                bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=message,
                    parse_mode='HTML'
                )
            
            sent_count += 1
            print(f"✅ [{sent_count}/{len(new_ids)}] Отправлен: {toy['name'][:50]}...")
            
            # Добавляем ID в список отправленных
            sent_ids.append(toy_id)
            
            # Сохраняем прогресс после каждого сообщения
            save_sent_items(sent_ids)
            
            # Важно: задержка между сообщениями (растет с каждым сообщением)
            if index < 20:
                time.sleep(3)  # первые 20 - пауза 3 сек
            else:
                time.sleep(5)  # потом пауза 5 сек
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                # Если лимит - ждем сколько сказано
                import re
                match = re.search(r'retry after (\d+)', error_str)
                if match:
                    wait_time = int(match.group(1)) + 1
                    print(f"⏳ Telegram просит подождать {wait_time} сек...")
                    time.sleep(wait_time)
                    # Пробуем снова отправить этот же товар
                    # Для этого не добавляем ID в sent_ids и повторяем цикл
                    continue
                else:
                    wait_time = 10
                    print(f"⏳ Лимит, ждем {wait_time} сек...")
                    time.sleep(wait_time)
                    continue
            else:
                print(f"❌ Ошибка: {error_str}")
                time.sleep(2)
    
    # Финальное сохранение
    save_sent_items(sent_ids)
    print(f"💾 Готово! Отправлено: {sent_count}, всего в списке: {len(sent_ids)}")