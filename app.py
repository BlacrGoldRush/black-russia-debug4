import os
import logging
import requests
import re
from flask import Flask
from bs4 import BeautifulSoup
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

def parse_black_russia_funpay():
    """Парсинг ВСЕХ товаров и анализ фильтрации"""
    try:
        url = "https://funpay.com/chips/186/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        logger.info("🎯 Парсинг ВСЕХ товаров на FunPay...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP ошибка: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем ВСЕ карточки товаров
        cards = soup.find_all('a', class_='tc-item')
        logger.info(f"📦 Найдено карточек товаров: {len(cards)}")
        
        all_items = []
        black_russia_items = []
        
        # Обрабатываем первые 30 карточек для анализа
        for card in cards[:30]:
            try:
                # 1. Извлекаем название
                title_elem = card.find('div', class_='tc-desc-text')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # 2. Логируем ВСЕ названия для анализа
                logger.info(f"   📝 Название товара: '{title}'")
                
                # 3. Извлекаем цену
                price_elem = card.find('div', class_='tc-price')
                if not price_elem:
                    continue
                
                price_text = price_elem.get_text(strip=True)
                
                # Извлекаем цифры из цены
                digits = re.findall(r'\d+', price_text.replace(' ', '').replace(' ', ''))
                if not digits:
                    continue
                
                price = int(''.join(digits))
                
                # Фильтр по цене
                if price < 10 or price > 50000:
                    continue
                
                # 4. Извлекаем ссылку
                href = card.get('href', '')
                if href.startswith('/'):
                    link = f"https://funpay.com{href}"
                else:
                    link = href
                
                # 5. Проверяем онлайн статус
                seller_online = card.get('data-online') == '1'
                
                item_data = {
                    'title': title[:150],
                    'price': price,
                    'link': link,
                    'seller_online': seller_online,
                    'seller_id': card.get('data-user', ''),
                    'raw_price_text': price_text
                }
                
                all_items.append(item_data)
                
                # 6. Пробуем разные варианты фильтрации
                title_lower = title.lower()
                
                # Варианты написания Black Russia
                patterns = [
                    'black russia', 'blackrussia', 'блек раша', 'блэк раша',
                    'блек рашн', 'блэк рашн', 'br ', 'бр ',
                    'black', 'russia', 'раша', 'рашн'
                ]
                
                # Проверяем каждый паттерн
                for pattern in patterns:
                    if pattern in title_lower:
                        black_russia_items.append(item_data)
                        logger.info(f"   ✅ Найден Black Russia по паттерну '{pattern}': '{title[:50]}...'")
                        break
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка обработки карточки: {e}")
                continue
        
        # Анализ результатов
        logger.info("📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
        logger.info(f"   Всего обработано карточек: {len(all_items)}")
        logger.info(f"   Из них Black Russia: {len(black_russia_items)}")
        
        if all_items and not black_russia_items:
            logger.info("   🔍 Примеры названий всех товаров:")
            for i, item in enumerate(all_items[:10]):
                logger.info(f"      {i+1}. '{item['title']}' - {item['price']} руб.")
        
        return black_russia_items
        
    except Exception as e:
        logger.error(f"💥 Ошибка парсинга: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def parse_all_without_filter():
    """Парсинг БЕЗ фильтрации - показываем ВСЕ товары"""
    try:
        url = "https://funpay.com/chips/186/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        logger.info("🔍 Парсинг ВСЕХ товаров БЕЗ фильтра...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('a', class_='tc-item')[:20]  # Только 20
        
        items = []
        
        for card in cards:
            try:
                title_elem = card.find('div', class_='tc-desc-text')
                price_elem = card.find('div', class_='tc-price')
                
                if not title_elem or not price_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                price_text = price_elem.get_text(strip=True)
                
                digits = re.findall(r'\d+', price_text.replace(' ', ''))
                if not digits:
                    continue
                
                price = int(''.join(digits))
                
                href = card.get('href', '')
                link = f"https://funpay.com{href}" if href.startswith('/') else href
                
                items.append({
                    'title': title[:100],
                    'price': price,
                    'link': link,
                    'online': card.get('data-online') == '1'
                })
                
            except:
                continue
        
        return items
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return []

# Маршруты Flask
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>FunPay Hunter - Анализ фильтрации</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .btn { display: inline-block; padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .btn-green { background: #28a745; }
            .btn-orange { background: #fd7e14; }
            .card { border: 1px solid #ddd; padding: 15px; margin: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🔍 FunPay Hunter - Анализ фильтрации</h1>
        <p><strong>Проблема:</strong> Найдено 11805 карточек, но 0 Black Russia</p>
        <p><strong>Задача:</strong> Узнать реальные названия товаров</p>
        
        <h3>Действия:</h3>
        <a href="/parse_debug" class="btn btn-orange">📝 Анализ названий</a>
        <a href="/parse_all" class="btn">📦 Показать ВСЕ товары</a>
        
        <h3>Что будет:</h3>
        <ol>
            <li>Парсер выведет в логи реальные названия товаров</li>
            <li>Мы увидим, какие слова действительно используются</li>
            <li>Настроим правильные ключевые слова</li>
        </ol>
    </body>
    </html>
    '''

@app.route('/parse_debug')
def parse_debug():
    """Страница анализа названий"""
    items = parse_black_russia_funpay()
    
    result = '''
    <div style="background: #d1ecf1; padding: 20px; border-radius: 5px;">
        <h2>✅ Анализ выполнен</h2>
        <p>Проверьте логи в Render Dashboard (вкладка Logs).</p>
        <p>Там будут ВСЕ названия товаров, которые наш парсер видит.</p>
        <p><strong>Пришлите мне эти логи!</strong></p>
        <p>Я увижу реальные названия и настрою правильную фильтрацию.</p>
    </div>
    
    <h3>Что ищем в логах:</h3>
    <ul>
        <li>Строки начинающиеся с "📝 Название товара:"</li>
        <li>Это реальные названия товаров с FunPay</li>
        <li>По ним поймем какие ключевые слова использовать</li>
    </ul>
    '''
    
    if items:
        result += f"<h3>✅ Найдено товаров Black Russia: {len(items)}</h3>"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Анализ названий</title></head>
    <body style="font-family: Arial; margin: 20px;">
        <a href="/">← Назад</a>
        {result}
    </body>
    </html>
    '''

@app.route('/parse_all')
def parse_all():
    """Показать ВСЕ товары без фильтра"""
    items = parse_all_without_filter()
    
    if items:
        result = f"<h2>📦 Все товары (первые {len(items)}):</h2>"
        
        for item in items:
            online_badge = "🟢 ОНЛАЙН" if item['online'] else "🔴 ОФФЛАЙН"
            result += f'''
            <div class="card">
                <h4>{item['title']}</h4>
                <p><strong>Цена:</strong> {item['price']} руб.</p>
                <p><strong>Статус:</strong> {online_badge}</p>
                <p><a href="{item['link']}" target="_blank">Открыть</a></p>
            </div>
            '''
    else:
        result = '''
        <div style="background: #f8d7da; padding: 20px; border-radius: 5px;">
            <h2>❌ Товары не найдены</h2>
            <p>Попробуйте позже или проверьте подключение.</p>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Все товары</title>
        <style>
            body {{ font-family: Arial; margin: 20px; }}
            .card {{ border: 1px solid #ddd; padding: 15px; margin: 10px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <a href="/">← Назад</a>
        {result}
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return "OK"

# Запуск приложения
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
