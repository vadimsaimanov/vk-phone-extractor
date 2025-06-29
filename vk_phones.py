import requests
import re
import pandas as pd
from urllib.parse import urlparse
from bs4 import BeautifulSoup

VK_TOKEN = '46e7acb546e7acb546e7acb58945d7ac65446e746e7acb52eef61dbb04191d1d078e7c5'
API_VERSION = '5.131'
INPUT_FILE = 'profiles.txt'
OUTPUT_FILE = 'vk_phones.xlsx'


def is_valid_phone(phone):
    if not phone or phone == "Not found":
        return False

    # Убираем всё, кроме цифр и +
    clean_phone = re.sub(r'[^\d+]', '', phone)

    # Если номер слишком короткий или слишком длинный — пропускаем
    if len(clean_phone) < 8 or len(clean_phone) > 15:
        return False

    # Исключаем номера, которые начинаются с +2, +3, +4 (нереальные для телефонов)
    if re.match(r'^\+[234]\d+', clean_phone):
        return False

    # Российские номера: +7XXXXXXXXXX или 8XXXXXXXXXX (11 цифр)
    if re.match(r'^(\+7|8)\d{10}$', clean_phone):
        return True

    # Международные номера: +XXX... (от 8 до 15 цифр, но не +2013, +1999 и т.д.)
    if re.match(r'^\+[5-9]\d{7,14}$', clean_phone):
        return True

    return False


def extract_vk_id(url):
    path = urlparse(url).path.strip('/')
    return path[2:] if path.startswith('id') else path


def get_phone_from_html(profile_url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(profile_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем телефон в мета-тегах или контактах
        phones = re.findall(r'[\+\(]?[0-9][0-9\-\(\)\.]{7,}[0-9]', str(soup))
        for phone in phones:
            if is_valid_phone(phone):
                return phone
        return None
    except Exception as e:
        print(f"Ошибка парсинга {profile_url}: {e}")
        return None


def get_phone_from_api(user_id):
    try:
        url = 'https://api.vk.com/method/users.get'
        params = {
            'user_ids': user_id,
            'fields': 'contacts',
            'access_token': VK_TOKEN,
            'v': API_VERSION
        }
        response = requests.get(url, params=params)
        data = response.json()

        if 'response' in data and data['response']:
            user = data['response'][0]
            phone = user.get('mobile_phone') or user.get('home_phone')
            return phone if is_valid_phone(phone) else None
        return None
    except Exception as e:
        print(f"Ошибка API для {user_id}: {e}")
        return None


def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    results = []
    for url in urls:
        vk_id = extract_vk_id(url)
        phone = None

        # Сначала пробуем API
        if VK_TOKEN:
            phone = get_phone_from_api(vk_id)

        # Если API не дал результат, парсим HTML
        if not phone:
            phone = get_phone_from_html(url)

        results.append({'URL': url, 'Phone': phone or 'Not found'})
        print(f"Processed: {url} -> {phone or 'No phone'}")

    pd.DataFrame(results).to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Результаты сохранены в {OUTPUT_FILE}")


if __name__ == '__main__':
    main()