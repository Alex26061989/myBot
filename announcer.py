# announcer.py
import time
import json
import os
from datetime import datetime
import telebot
from data import TOYS

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
    """ВРЕМЕННО: всегда возвращаем пустой список, чтобы отправить всё заново"""
    print("⚠️ ВРЕМЕННО: сбрасываем историю отправок")
    return []  # Всегда говорим, что ничего не отправлено

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
    """Создает красивое сообщение для канала"""
    
    # Определяем иконку по возрасту
    age_icon = "👶" if "0-1" in toy['age'] else "🧒" if "1-3" in toy['age'] else "👦"
    
    # Определяем категорию по типу
    type_icons = {
        'logic': '🧩',
        'learning': '📚',
        'construction': '🏗️',
        'creativity': '🎨',
        'movement': '🏃',
        'music': '🎵',
        'profession': '👨‍⚕️'
    }
    
    # Собираем иконки для всех типов игрушки
    icons = [type_icons.get(t, '🎁') for t in toy['type']]
    type_icon = ' '.join(icons[:3])  # берем первые 3 типа
    
    # Формируем сообщение
    message = f"<b>🆕 НОВИНКА В НАШЕМ КАТАЛОГЕ!</b>\n\n"
    message += f"<b>{toy['name']}</b>\n\n"
    
    # Описание (первые 200 символов)
    if isinstance(toy['description'], dict):
        desc = list(toy['description'].values())[0]
    else:
        desc = str(toy['description'])
    
    short_desc = desc[:200] + "..." if len(desc) > 200 else desc
    message += f"<i>{short_desc}</i>\n\n"
    
    # Характеристики
    message += f"💰 <b>Цена:</b> {format_price(toy['price'])}\n"
    message += f"{age_icon} <b>Возраст:</b> {', '.join(toy['age'])} лет\n"
    message += f"{type_icon} <b>Категория:</b> {', '.join(toy['type'])}\n\n"
    
    # Кнопка для перехода в бота
    message += f"👇 <b>Забрать игрушку можно в нашем боте:</b>\n"
    message += f"👉 <a href='https://t.me/ToyChoiseBot'>@ToyChoiseBot</a>\n\n"
    
    # Хэштеги
    hashtags = [f"#{t}" for t in toy['type']]
    hashtags.append(f"#{toy['age'][0].replace('-', '_')}")
    message += " ".join(hashtags)
    
    return message

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