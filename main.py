#!/usr/bin/env python3
"""
Основной файл для запуска парсера отзывов
Поддерживает автоматический парсинг по расписанию и ручной запуск
"""

import argparse
import sys
import time
import logging
import re
import os
from core.review_scheduler import ReviewScheduler
from core.config import *
from parsers.multi_page_yandex_parser import MultiPageYandexParser
from parsers.simple_twogis_parser import SimpleTwoGisParser
import pandas as pd

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('parser.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_unified_csv():
    """Создание единого CSV файла из всех источников"""
    logger = logging.getLogger('UnifiedCSV')
    
    try:
        # Проверяем наличие файлов
        yandex_file = 'data/url_reviews.csv'
        twogis_file = 'data/twogis_reviews.csv'
        
        if not os.path.exists(yandex_file) and not os.path.exists(twogis_file):
            logger.warning("Нет файлов с отзывами для объединения")
            return
        
        # Читаем доступные файлы
        dataframes = []
        
        if os.path.exists(yandex_file):
            yandex_df = pd.read_csv(yandex_file)
            yandex_df['id'] = ['yandex_' + f"{i:03d}" for i in range(len(yandex_df))]
            dataframes.append(yandex_df)
            logger.info(f"✅ Загружено {len(yandex_df)} отзывов из Yandex")
        
        if os.path.exists(twogis_file):
            twogis_df = pd.read_csv(twogis_file)
            twogis_df['id'] = ['twogis_' + f"{i:03d}" for i in range(len(twogis_df))]
            dataframes.append(twogis_df)
            logger.info(f"✅ Загружено {len(twogis_df)} отзывов из 2ГИС")
        
        if not dataframes:
            logger.warning("Нет данных для объединения")
            return
        
        # Объединяем данные
        merged_df = pd.concat(dataframes, ignore_index=True)
        
        # Сортируем по источнику, затем по ID
        merged_df = merged_df.sort_values(['source', 'id']).reset_index(drop=True)
        
        # Сохраняем объединенный файл
        output_file = 'data/all_reviews.csv'
        merged_df.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"💾 Создан объединенный файл: {output_file} ({len(merged_df)} отзывов)")
        
        # Статистика
        source_stats = merged_df['source'].value_counts()
        logger.info("📊 Статистика по источникам:")
        for source, count in source_stats.items():
            logger.info(f"   {source}: {count} отзывов")
        
        return len(merged_df)
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания объединенного файла: {e}")
        return 0

def parallel_parse_urls(yandex_url: str, twogis_url: str):
    """Параллельный парсинг отзывов с Yandex и 2ГИС"""
    logger = logging.getLogger('ParallelParser')
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def parse_yandex():
        """Парсинг Yandex"""
        try:
            logger.info(f"🌐 Запуск парсинга Yandex: {yandex_url}")
            parser = MultiPageYandexParser()
            reviews = parser.parse_reviews_from_url(yandex_url, limit=150, max_pages=5)
            parser.save_reviews_to_csv(reviews, "data/url_reviews.csv")
            logger.info(f"✅ Yandex: найдено {len(reviews)} отзывов")
            return len(reviews)
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Yandex: {e}")
            return 0
    
    def parse_twogis():
        """Парсинг 2ГИС"""
        try:
            logger.info(f"🌐 Запуск парсинга 2ГИС: {twogis_url}")
            parser = SimpleTwoGisParser()
            reviews = parser.parse_reviews_from_url(twogis_url, limit=150)
            parser.save_reviews_to_csv(reviews, "data/twogis_reviews.csv")
            logger.info(f"✅ 2ГИС: найдено {len(reviews)} отзывов")
            return len(reviews)
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга 2ГИС: {e}")
            return 0
    
    # Запускаем парсинг параллельно
    logger.info("🚀 Запуск параллельного парсинга...")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Запускаем оба парсера одновременно
        yandex_future = executor.submit(parse_yandex)
        twogis_future = executor.submit(parse_twogis)
        
        # Ждем завершения и получаем результаты
        yandex_count = yandex_future.result()
        twogis_count = twogis_future.result()
    
    # Создаем объединенный файл
    total_reviews = create_unified_csv()
    
    logger.info(f"🎉 Параллельный парсинг завершен!")
    logger.info(f"   Yandex: {yandex_count} отзывов")
    logger.info(f"   2ГИС: {twogis_count} отзывов")
    logger.info(f"   Всего: {total_reviews} отзывов")
    
    return {
        'yandex': yandex_count,
        '2gis': twogis_count,
        'total': total_reviews
    }

def main():
    """Основная функция"""
    setup_logging()
    logger = logging.getLogger('Main')
    
    parser = argparse.ArgumentParser(description='Парсер отзывов с Yandex карт и 2GIS')
    
    # Аргументы командной строки
    parser.add_argument('--business', '-b', type=str, help='Название бизнеса для парсинга')
    parser.add_argument('--url', '-u', type=str, help='URL страницы с отзывами для парсинга')
    parser.add_argument('--sources', '-s', nargs='+', choices=['yandex', '2gis'], 
                       default=['yandex', '2gis'], help='Источники для парсинга')
    parser.add_argument('--schedule', action='store_true', help='Запустить планировщик')
    parser.add_argument('--interval', '-i', type=int, default=SCHEDULE_INTERVAL_MINUTES,
                       help=f'Интервал парсинга в минутах (по умолчанию: {SCHEDULE_INTERVAL_MINUTES})')
    parser.add_argument('--add-business', '-a', type=str, help='Добавить бизнес в список для планировщика')
    parser.add_argument('--add-url', type=str, help='Добавить URL в список для планировщика')
    parser.add_argument('--status', action='store_true', help='Показать статус планировщика')
    parser.add_argument('--parallel', action='store_true', help='Параллельный парсинг Yandex и 2ГИС')
    
    args = parser.parse_args()
    
    # Создаем планировщик
    scheduler = ReviewScheduler()
    
    try:
        if args.add_business:
            # Добавляем бизнес в список
            scheduler.add_business(args.add_business, args.sources)
            logger.info(f"Бизнес '{args.add_business}' добавлен в список для планировщика")
            
        elif args.add_url:
            # Добавляем URL в список
            scheduler.add_business("URL Business", sources=[], url=args.add_url)
            logger.info(f"URL '{args.add_url}' добавлен в список для планировщика")
            
        elif args.status:
            # Показываем статус
            status = scheduler.get_status()
            print("\n=== СТАТУС ПЛАНИРОВЩИКА ===")
            print(f"Запущен: {'Да' if status['is_running'] else 'Нет'}")
            print(f"Количество бизнесов: {status['businesses_count']}")
            print(f"Интервал: {status['interval_minutes']} минут")
            if status['next_run']:
                print(f"Следующий запуск: {status['next_run']}")
            else:
                print("Следующий запуск: Не запланирован")
            print("========================\n")
            
        elif args.schedule:
            # Запускаем планировщик
            if not scheduler.businesses:
                logger.error("Нет бизнесов для планировщика. Используйте --add-business для добавления")
                return
                
            logger.info("Запуск планировщика...")
            scheduler_thread = scheduler.start_scheduler()
            
            print(f"\nПланировщик запущен с интервалом {args.interval} минут")
            print("Нажмите Ctrl+C для остановки")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки...")
                scheduler.stop_scheduler()
                print("Планировщик остановлен")

        elif args.url:
            # Немедленный парсинг по URL
            logger.info(f"Запуск парсинга по URL: {args.url}")
            
            # Проверяем, это Yandex или 2ГИС
            if 'yandex.ru' in args.url:
                # Парсинг Yandex
                business_id_match = re.search(r'/org/[^/]+/(\d+)', args.url)
                if business_id_match:
                    business_id = business_id_match.group(1)
                    business_name_match = re.search(r'/org/([^/]+)/', args.url)
                    business_name = business_name_match.group(1) if business_name_match else "business"
                    
                    # Используем многопоточный парсер с поддержкой пагинации
                    parser = MultiPageYandexParser()
                    reviews = parser.parse_reviews_from_url(args.url, limit=150, max_pages=5)
                    parser.save_reviews_to_csv(reviews, "data/url_reviews.csv")
                    
                    # Создаем объединенный файл
                    total_reviews = create_unified_csv()
                    
                    print(f"\n=== РЕЗУЛЬТАТЫ ПАРСИНГА YANDEX ===")
                    print(f"URL: {args.url}")
                    print(f"Бизнес: {business_name}")
                    print(f"ID: {business_id}")
                    print(f"Найдено отзывов: {len(reviews)}")
                    print("Отзывы сохранены в: data/url_reviews.csv")
                    print(f"Объединенный файл: data/all_reviews.csv ({total_reviews} отзывов)")
                    print("===============================\n")
                else:
                    print("❌ Не удалось извлечь ID бизнеса из URL Yandex")
                    print("Убедитесь, что URL содержит путь /org/name/id/")
                    
            elif '2gis.ru' in args.url:
                # Парсинг 2ГИС с автообновлением
                business_id_match = re.search(r'/firm/(\d+)', args.url)
                if business_id_match:
                    business_id = business_id_match.group(1)
                    
                    # Используем простой парсер 2ГИС
                    parser = SimpleTwoGisParser()
                    reviews = parser.parse_reviews_from_url(args.url, limit=150)
                    parser.save_reviews_to_csv(reviews, "data/twogis_reviews.csv")
                    
                    # Создаем объединенный файл
                    total_reviews = create_unified_csv()
                    
                    print(f"\n=== РЕЗУЛЬТАТЫ ПАРСИНГА 2ГИС ===")
                    print(f"URL: {args.url}")
                    print(f"Бизнес ID: {business_id}")
                    print(f"Найдено отзывов: {len(reviews)}")
                    print("Отзывы сохранены в: data/twogis_reviews.csv")
                    print(f"Объединенный файл: data/all_reviews.csv ({total_reviews} отзывов)")
                    print("===============================\n")
                    
                else:
                    print("❌ Не удалось извлечь ID бизнеса из URL 2ГИС")
                    print("Убедитесь, что URL содержит путь /firm/id/")
            else:
                print("❌ Неподдерживаемый URL")
                print("Поддерживаются только yandex.ru и 2gis.ru")
            
        elif args.parallel:
            # Параллельный парсинг Yandex и 2ГИС
            yandex_url = "https://yandex.ru/maps/org/galki/115736401897/reviews/"
            twogis_url = "https://2gis.ru/moscow/search/Галки/firm/70000001040039867/37.60904%2C55.764912/tab/reviews"
            
            logger.info("Запуск параллельного парсинга Yandex и 2ГИС")
            result = parallel_parse_urls(yandex_url, twogis_url)
            
            print(f"\n=== РЕЗУЛЬТАТЫ ПАРАЛЛЕЛЬНОГО ПАРСИНГА ===")
            print(f"Yandex: {result['yandex']} отзывов")
            print(f"2ГИС: {result['2gis']} отзывов")
            print(f"Всего: {result['total']} отзывов")
            print("Отзывы сохранены в:")
            print("  - data/url_reviews.csv (Yandex)")
            print("  - data/twogis_reviews.csv (2ГИС)")
            print("  - data/all_reviews.csv (объединенный)")
            print("==========================================\n")
            
        elif args.business:
            # Немедленный парсинг конкретного бизнеса
            logger.info(f"Запуск парсинга для бизнеса: {args.business}")
            result = scheduler.run_immediate_parsing(args.business, args.sources)
            
            print(f"\n=== РЕЗУЛЬТАТЫ ПАРСИНГА ===")
            print(f"Бизнес: {args.business}")
            for source, count in result.items():
                print(f"{source}: {count} отзывов")
            print("========================\n")
            
        else:
            # Показываем справку
            parser.print_help()
            print("\nПримеры использования:")
            print("1. Парсинг конкретного бизнеса:")
            print("   python main.py --business 'Кафе Пушкин'")
            print("\n2. Парсинг по URL Yandex:")
            print("   python main.py --url 'https://yandex.ru/maps/org/galki/115736401897/reviews/'")
            print("\n3. Парсинг по URL 2ГИС:")
            print("   python main.py --url 'https://2gis.ru/moscow/search/Галки/firm/70000001040039867/37.60904%2C55.764912/tab/reviews'")
            print("\n4. Добавление бизнеса в планировщик:")
            print("   python main.py --add-business 'Кафе Пушкин'")
            print("\n5. Добавление URL в планировщик:")
            print("   python main.py --add-url 'https://yandex.ru/maps/org/galki/115736401897/reviews/'")
            print("\n6. Запуск планировщика:")
            print("   python main.py --schedule")
            print("\n7. Парсинг только с Yandex:")
            print("   python main.py --business 'Кафе Пушкин' --sources yandex")
            print("\n8. Параллельный парсинг Yandex и 2ГИС:")
            print("   python main.py --parallel")
            
    except Exception as e:
        logger.error(f"Ошибка выполнения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()