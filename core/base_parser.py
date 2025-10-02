import requests
import csv
import json
import time
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import threading
import sys
from .config import *

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('parser.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
)

class Review:
    """Класс для представления отзыва"""
    def __init__(self, text: str, rating: int, author: str, date: str, source: str):
        self.text = text
        self.rating = rating
        self.author = author
        self.date = date
        self.source = source
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'rating': self.rating,
            'author': self.author,
            'date': self.date,
            'source': self.source,
            'timestamp': self.timestamp
        }

class BaseParser(ABC):
    """Базовый класс для парсеров отзывов"""
    
    def __init__(self, business_name: str, business_id: Optional[str] = None):
        self.business_name = business_name
        self.business_id = business_id
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.lock = threading.Lock()
        
    @abstractmethod
    def get_reviews(self, limit: int = MAX_REVIEWS_PER_REQUEST) -> List[Review]:
        """Получить отзывы с сайта"""
        pass
    
    @abstractmethod
    def search_business(self, name: str) -> Optional[str]:
        """Найти бизнес по имени и получить ID"""
        pass
    
    def save_to_csv(self, reviews: List[Review], filename: str):
        """Сохранить отзывы в CSV файл"""
        if not reviews:
            self.logger.warning("Нет отзывов для сохранения")
            return
            
        filepath = os.path.join(CSV_OUTPUT_DIR, filename)
        
        with self.lock:
            file_exists = os.path.exists(filepath)
            
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['text', 'rating', 'author', 'date', 'source', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                for review in reviews:
                    writer.writerow(review.to_dict())
        
        self.logger.info(f"Сохранено {len(reviews)} отзывов в {filepath}")
    
    def make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """Выполнить HTTP запрос с обработкой ошибок"""
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            time.sleep(REQUEST_DELAY_SECONDS)
            return response
        except requests.RequestException as e:
            self.logger.error(f"Ошибка запроса к {url}: {e}")
            return None
