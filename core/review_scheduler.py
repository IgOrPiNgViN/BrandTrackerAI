import threading
import time
import schedule
from datetime import datetime
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_parser import Review
from parsers.multi_page_yandex_parser import MultiPageYandexParser
from parsers.simple_twogis_parser import SimpleTwoGisParser
from .config import *

class ReviewScheduler:
    """Планировщик для автоматического парсинга отзывов"""
    
    def __init__(self):
        self.logger = logging.getLogger('ReviewScheduler')
        self.is_running = False
        self.businesses = []  # Список бизнесов для парсинга
        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
        
    def add_business(self, name: str, sources: List[str] = None, url: str = None):
        """Добавить бизнес для парсинга"""
        if sources is None:
            sources = ['yandex', '2gis']
            
        business_config = {
            'name': name,
            'sources': sources,
            'url': url
        }
        self.businesses.append(business_config)
        self.logger.info(f"Добавлен бизнес: {name} для источников: {sources}")
    
    def parse_business_reviews(self, business_config: Dict) -> Dict:
        """Парсинг отзывов для одного бизнеса"""
        business_name = business_config['name']
        sources = business_config['sources']
        url = business_config.get('url')
        results = {}
        
        self.logger.info(f"Начинаем парсинг отзывов для: {business_name}")
        
        # Если есть URL, используем URL парсер
        if url:
            try:
                if 'yandex.ru' in url:
                    parser = MultiPageYandexParser()
                    reviews = parser.parse_reviews_from_url(url, limit=150, max_pages=5)
                elif '2gis.ru' in url:
                    parser = SimpleTwoGisParser()
                    reviews = parser.parse_reviews_from_url(url, limit=150)
                else:
                    self.logger.warning(f"❌ Неподдерживаемый URL: {url}")
                    return results
                
                # Сохраняем в соответствующий файл
                if 'yandex.ru' in url:
                    parser.save_reviews_to_csv(reviews, CSV_FILENAME_YANDEX)
                    results['yandex'] = len(reviews)
                elif '2gis.ru' in url:
                    parser.save_reviews_to_csv(reviews, CSV_FILENAME_2GIS)
                    results['2gis'] = len(reviews)
                    
            except Exception as e:
                self.logger.error(f"Ошибка парсинга по URL для {business_name}: {e}")
                results['url'] = 0
        else:
            # Обычный парсинг по источникам
            for source in sources:
                try:
                    if source.lower() == 'yandex':
                        # Для Yandex нужен URL, используем базовый парсер
                        parser = MultiPageYandexParser()
                        # Здесь нужно будет добавить логику поиска URL по имени бизнеса
                        self.logger.warning("Парсинг Yandex по имени бизнеса требует URL")
                        results['yandex'] = 0
                        
                    elif source.lower() == '2gis':
                        # Для 2ГИС нужен URL, используем базовый парсер
                        parser = SimpleTwoGisParser()
                        # Здесь нужно будет добавить логику поиска URL по имени бизнеса
                        self.logger.warning("Парсинг 2ГИС по имени бизнеса требует URL")
                        results['2gis'] = 0
                        
                except Exception as e:
                    self.logger.error(f"Ошибка парсинга {source} для {business_name}: {e}")
                    results[source] = 0
        
        self.logger.info(f"Завершен парсинг для {business_name}: {results}")
        return results
    
    def run_scheduled_parsing(self):
        """Запуск запланированного парсинга"""
        if not self.businesses:
            self.logger.warning("Нет бизнесов для парсинга")
            return
            
        self.logger.info(f"Запуск запланированного парсинга для {len(self.businesses)} бизнесов")
        
        # Используем ThreadPoolExecutor для многопоточного парсинга
        futures = []
        
        for business_config in self.businesses:
            future = self.executor.submit(self.parse_business_reviews, business_config)
            futures.append(future)
        
        # Ждем завершения всех задач
        total_reviews = {'yandex': 0, '2gis': 0}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                for source, count in result.items():
                    total_reviews[source] += count
            except Exception as e:
                self.logger.error(f"Ошибка выполнения задачи: {e}")
        
        self.logger.info(f"Запланированный парсинг завершен. Всего отзывов: {total_reviews}")
    
    def start_scheduler(self):
        """Запуск планировщика"""
        if self.is_running:
            self.logger.warning("Планировщик уже запущен")
            return
            
        self.is_running = True
        
        # Настраиваем расписание
        schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(self.run_scheduled_parsing)
        
        self.logger.info(f"Планировщик запущен с интервалом {SCHEDULE_INTERVAL_MINUTES} минут")
        
        # Запускаем планировщик в отдельном потоке
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread
    
    def _run_scheduler(self):
        """Внутренний метод для запуска планировщика"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        self.is_running = False
        schedule.clear()
        self.executor.shutdown(wait=True)
        self.logger.info("Планировщик остановлен")
    
    def run_immediate_parsing(self, business_name: str = None, sources: List[str] = None):
        """Немедленный парсинг отзывов"""
        if business_name:
            # Парсинг конкретного бизнеса
            business_config = {
                'name': business_name,
                'sources': sources or ['yandex', '2gis']
            }
            return self.parse_business_reviews(business_config)
        else:
            # Парсинг всех бизнесов
            return self.run_scheduled_parsing()
    
    def get_status(self) -> Dict:
        """Получить статус планировщика"""
        return {
            'is_running': self.is_running,
            'businesses_count': len(self.businesses),
            'next_run': schedule.next_run() if schedule.jobs else None,
            'interval_minutes': SCHEDULE_INTERVAL_MINUTES
        }
