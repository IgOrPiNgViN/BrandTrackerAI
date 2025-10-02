# Конфигурация парсера отзывов
import os

# Настройки многопоточности
MAX_THREADS = 5
MIN_THREADS = 4

# Настройки планировщика
SCHEDULE_INTERVAL_MINUTES = 30  # Интервал парсинга в минутах

# Настройки файлов
CSV_OUTPUT_DIR = "data"
CSV_FILENAME_YANDEX = "yandex_reviews.csv"
CSV_FILENAME_2GIS = "2gis_reviews.csv"

# Настройки парсинга
MAX_REVIEWS_PER_REQUEST = 20
REQUEST_DELAY_SECONDS = 2  # Задержка между запросами

# User-Agent для запросов
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Дополнительные заголовки для обхода защиты
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}

# Создаем директорию для сохранения данных
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)