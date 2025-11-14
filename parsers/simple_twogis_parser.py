#!/usr/bin/env python3
"""
Простой парсер отзывов с 2ГИС из HTML файла
"""

import requests
import re
import os
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import csv

class SimpleTwoGisParser:
    """Простой парсер отзывов с 2ГИС"""

    def __init__(self):
        self.logger = logging.getLogger('SimpleTwoGisParser')

    def parse_reviews_from_url(self, url: str, limit: int = 1000, max_pages: int = 30) -> List[Dict]:
        """Парсинг отзывов с 2ГИС по URL"""
        self.logger.info(f"🌐 Парсинг отзывов с 2ГИС URL: {url} (лимит: {limit}, страниц: {max_pages})")
        
        # Извлекаем ID бизнеса
        business_id = self._extract_business_id(url)
        if not business_id:
            self.logger.error("❌ Не удалось извлечь ID бизнеса из URL")
            return []
        
        all_reviews = []
        review_counter = 0
        consecutive_empty_pages = 0
        
        for page in range(1, max_pages + 1):
            page_url = self._build_page_url(url, page)
            self.logger.info(f"📄 Загружаем страницу {page}: {page_url}")
            
            html_content = self._download_page(page_url)
            if not html_content:
                self.logger.warning(f"⚠️ Не удалось скачать страницу {page}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 3:
                    self.logger.info(f"⏹️ Прекращаем парсинг: 3 страницы подряд не удалось скачать")
                    break
                continue
            
            page_reviews = self._extract_reviews_from_html(html_content, business_id, limit, review_counter)
            
            if len(page_reviews) == 0:
                consecutive_empty_pages += 1
                self.logger.warning(f"⚠️ Страница {page}: найдено 0 отзывов (пустых страниц подряд: {consecutive_empty_pages})")
                if consecutive_empty_pages >= 3:
                    self.logger.info(f"⏹️ Прекращаем парсинг: достигнут конец отзывов (3 пустые страницы подряд)")
                    break
            else:
                consecutive_empty_pages = 0
                review_counter += len(page_reviews)
                all_reviews.extend(page_reviews)
                self.logger.info(f"📊 Страница {page}: найдено {len(page_reviews)} отзывов, всего: {len(all_reviews)}")
            
            if page < max_pages:
                import time
                import random
                from core.config import REQUEST_DELAY_SECONDS
                delay = random.uniform(REQUEST_DELAY_SECONDS, REQUEST_DELAY_SECONDS * 2)
                time.sleep(delay)
        
        self.logger.info(f"✅ Всего найдено отзывов: {len(all_reviews)}")
        return all_reviews

    def _extract_business_id(self, url: str) -> Optional[str]:
        """Извлечение ID бизнеса из URL 2ГИС"""
        match = re.search(r'/firm/(\d+)', url)
        return match.group(1) if match else None

    def _build_page_url(self, base_url: str, page: int) -> str:
        """Построение URL для конкретной страницы 2ГИС"""
        # Убираем существующие параметры пагинации
        base_url = re.sub(r'[?&]page=\d+', '', base_url)
        base_url = re.sub(r'[?&]p=\d+', '', base_url)
        
        # Для первой страницы возвращаем базовый URL
        if page == 1:
            return base_url
        
        # Добавляем параметр страницы
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page}"

    def _download_page(self, url: str) -> Optional[str]:
        """Скачивание страницы"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            self.logger.warning(f"❌ Ошибка скачивания {url}: {e}")
            return None

    def _extract_reviews_from_html(self, html_content: str, business_id: str, limit: int, start_counter: int = 0) -> List[Dict]:
        """Извлечение отзывов из HTML 2ГИС"""
        soup = BeautifulSoup(html_content, 'html.parser')
        reviews = []
        
        # Ищем блоки отзывов в 2ГИС по разным селекторам
        review_blocks = soup.find_all('div', class_='_1k5soqfl')
        
        # Альтернативные селекторы
        if not review_blocks:
            review_blocks = soup.find_all('div', attrs={'data-review-id': True})
        if not review_blocks:
            review_blocks = soup.find_all('div', class_=re.compile(r'review|Review|отзыв', re.I))
        
        self.logger.info(f"🔍 Найдено блоков отзывов: {len(review_blocks)}")
        
        for i, block in enumerate(review_blocks):
            try:
                # Извлекаем текст отзыва
                text_element = block.find('div', class_='_49x36f')
                
                # Альтернативные селекторы для текста
                if not text_element:
                    text_element = block.find('div', class_=re.compile(r'text|Text|текст', re.I))
                if not text_element:
                    # Ищем любой div с длинным текстом
                    text_elements = block.find_all('div')
                    for elem in text_elements:
                        text = elem.get_text(strip=True)
                        if 50 <= len(text) <= 5000:
                            text_element = elem
                            break
                
                if text_element:
                    text = text_element.get_text(strip=True)
                    
                    # Проверяем, что это отзыв гостя
                    if self._is_guest_review(text):
                        # Извлекаем данные
                        author = self._extract_author(block)
                        rating = self._extract_rating(block)
                        date = self._extract_date(block)
                        
                        # Нормализуем данные
                        author = self._clean_author_name(author)
                        date = self._clean_date_text(date)
                        
                        # Создаем уникальный ID
                        review_id = f"{business_id}_{start_counter + len(reviews)}"
                        
                        review = {
                            'id': review_id,
                            'text': text,
                            'rating': rating,
                            'author': author,
                            'date': date,
                            'source': '2GIS'
                        }
                        
                        reviews.append(review)
                        self.logger.debug(f"✅ Найден отзыв {len(reviews)}: {text[:50]}...")
                        
            except Exception as e:
                self.logger.debug(f"Ошибка обработки блока {i}: {e}")
                continue
        
        return reviews

    def _is_guest_review(self, text: str) -> bool:
        """Проверка, что это отзыв гостя (не ответ ресторана)"""
        if not text or not isinstance(text, str):
            return False
        
        text_lower = text.lower()
        
        # Исключаем ответы ресторана
        restaurant_response_keywords = [
            'спасибо за отзыв', 'благодарим за отзыв', 'рады что вам понравилось',
            'приносим извинения', 'мы работаем над', 'наша команда',
            'администрация ресторана', 'менеджер ресторана', 'управляющий',
            'мы ценим', 'мы стремимся', 'наша цель', 'мы стараемся',
            'вдохновляете', 'залетай на завтраки', 'обняли всей командой'
        ]
        
        if any(keyword in text_lower for keyword in restaurant_response_keywords):
            return False
        
        # Проверяем, что это не служебный текст (убрали 2gis, maps, http, https)
        not_service_text = not any(service_word in text_lower for service_word in [
            'cookie', 'javascript', 'script', 'function', 'var ', 'let ', 'const ',
            'html', 'css', 'class=', 'id=', 'href=', 'src=', 'alt=',
            'api', 'json', 'xml'
        ])
        
        # Более мягкие проверки
        has_spaces = ' ' in text
        has_letters = bool(re.search(r'[а-яёА-ЯЁa-zA-Z]', text))
        not_too_short = len(text) > 20  # Было 50
        not_too_long = len(text) < 5000  # Было 1000
        
        return (has_spaces and has_letters and not_too_short and not_too_long and not_service_text)

    def _extract_author(self, block) -> str:
        """Извлечение автора из блока 2ГИС"""
        try:
            # Ищем имя автора в правильном селекторе
            author_element = block.find('span', class_='_16s5yj36')
            if author_element:
                author_text = author_element.get_text(strip=True)
                cleaned = self._clean_author_name(author_text)
                if cleaned:
                    return cleaned
            
            return "Аноним"
        except:
            return "Аноним"

    def _clean_author_name(self, author_text: str) -> str:
        """Очистка имени автора"""
        try:
            # Убираем лишний текст
            unwanted_patterns = [
                r'Полезно\s*\d*',
                r'Читать целиком',
                r'Ответить',
                r'Пожаловаться',
                r'\s+',
                r'^\s+|\s+$'
            ]
            cleaned = author_text
            for pattern in unwanted_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
            # Убираем лишние пробелы и нормализуем
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            # Проверяем, что осталось что-то разумное
            if cleaned and len(cleaned) > 1 and len(cleaned) < 50 and re.search(r'[а-яёА-ЯЁa-zA-Z]', cleaned):
                return cleaned
            return ""
        except:
            return ""

    def _extract_rating(self, block) -> int:
        """Извлечение рейтинга из блока 2ГИС"""
        try:
            # Ищем SVG элементы со звёздами
            star_svgs = block.find_all('svg')
            for svg in star_svgs:
                # Подсчитываем заполненные звёзды по цвету
                paths = svg.find_all('path')
                filled_stars = 0
                for path in paths:
                    fill = path.get('fill', '')
                    if fill == 'black' or fill == '#000000':
                        filled_stars += 1
                
                if filled_stars > 0:
                    return min(filled_stars, 5)  # Максимум 5 звёзд
            
            return 0
        except:
            return 0

    def _extract_date(self, block) -> str:
        """Извлечение даты из блока 2ГИС"""
        try:
            # Ищем дату в правильном селекторе
            date_element = block.find('div', class_='_1evjsdb')
            if date_element:
                date_text = date_element.get_text(strip=True)
                # Убираем "официальный ответ" если есть
                date_text = re.sub(r',\s*официальный ответ', '', date_text, flags=re.IGNORECASE)
                cleaned_date = self._clean_date_text(date_text)
                if cleaned_date:
                    return cleaned_date
            
            # Если дата не найдена, возвращаем текущую дату
            from datetime import datetime
            return datetime.now().strftime('%Y-%m-%d')
        except:
            # В случае ошибки возвращаем текущую дату
            from datetime import datetime
            return datetime.now().strftime('%Y-%m-%d')

    def _clean_date_text(self, date_text: str) -> str:
        """Очистка текста даты и конвертация в числовой формат YYYY-MM-DD"""
        try:
            # Если уже в правильном формате YYYY-MM-DD, возвращаем как есть
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_text.strip()):
                return date_text.strip()
            
            # Паттерны для поиска даты (русские и английские)
            date_patterns = [
                r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}',
                r'\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|january|february|march|april|may|june|july|august|september|october|november|december)',
                r'\d{1,2}\.\d{1,2}\.\d{4}',
                r'(вчера|сегодня|позавчера)',
                r'\d+\s+(дня|дней|недели|недель|месяца|месяцев|года|лет)\s+назад'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text, re.IGNORECASE)
                if match:
                    found_date = match.group(0)
                    # Конвертируем в числовой формат
                    return self._convert_to_numeric_date(found_date)
            
            # Если ничего не найдено, возвращаем текущую дату
            from datetime import datetime
            return datetime.now().strftime('%Y-%m-%d')
        except:
            # В случае ошибки возвращаем текущую дату
            from datetime import datetime
            return datetime.now().strftime('%Y-%m-%d')

    def _convert_to_numeric_date(self, date_text: str) -> str:
        """Конвертация текстовой даты в числовой формат YYYY-MM-DD"""
        try:
            from datetime import datetime, timedelta
            
            # Словарь месяцев (русские и английские)
            months = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            # Обработка относительных дат
            if 'сегодня' in date_text.lower():
                return datetime.now().strftime('%Y-%m-%d')
            elif 'вчера' in date_text.lower():
                yesterday = datetime.now() - timedelta(days=1)
                return yesterday.strftime('%Y-%m-%d')
            elif 'позавчера' in date_text.lower():
                day_before_yesterday = datetime.now() - timedelta(days=2)
                return day_before_yesterday.strftime('%Y-%m-%d')
            
            # Обработка "X дней назад"
            days_ago_match = re.search(r'(\d+)\s+(дня|дней)\s+назад', date_text.lower())
            if days_ago_match:
                days = int(days_ago_match.group(1))
                past_date = datetime.now() - timedelta(days=days)
                return past_date.strftime('%Y-%m-%d')
            
            # Обработка "X недель назад"
            weeks_ago_match = re.search(r'(\d+)\s+(недели|недель)\s+назад', date_text.lower())
            if weeks_ago_match:
                weeks = int(weeks_ago_match.group(1))
                past_date = datetime.now() - timedelta(weeks=weeks)
                return past_date.strftime('%Y-%m-%d')
            
            # Обработка "X месяцев назад"
            months_ago_match = re.search(r'(\d+)\s+(месяца|месяцев)\s+назад', date_text.lower())
            if months_ago_match:
                months_count = int(months_ago_match.group(1))
                # Приблизительно 30 дней в месяце
                past_date = datetime.now() - timedelta(days=months_count * 30)
                return past_date.strftime('%Y-%m-%d')
            
            # Обработка "X лет назад"
            years_ago_match = re.search(r'(\d+)\s+(года|лет)\s+назад', date_text.lower())
            if years_ago_match:
                years = int(years_ago_match.group(1))
                past_date = datetime.now() - timedelta(days=years * 365)
                return past_date.strftime('%Y-%m-%d')
            
            # Обработка полной даты с годом: "2 мая 2024"
            full_date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
            if full_date_match:
                day = int(full_date_match.group(1))
                month_name = full_date_match.group(2).lower()
                year = int(full_date_match.group(3))
                
                if month_name in months:
                    month = months[month_name]
                    return f"{year:04d}-{month:02d}-{day:02d}"
            
            # Обработка даты без года: "2 мая" (предполагаем текущий год)
            date_without_year_match = re.search(r'(\d{1,2})\s+(\w+)', date_text)
            if date_without_year_match:
                day = int(date_without_year_match.group(1))
                month_name = date_without_year_match.group(2).lower()
                
                if month_name in months:
                    month = months[month_name]
                    current_year = datetime.now().year
                    return f"{current_year:04d}-{month:02d}-{day:02d}"
            
            # Обработка формата DD.MM.YYYY
            dot_date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_text)
            if dot_date_match:
                day = int(dot_date_match.group(1))
                month = int(dot_date_match.group(2))
                year = int(dot_date_match.group(3))
                return f"{year:04d}-{month:02d}-{day:02d}"
            
            # Если ничего не подошло, возвращаем исходный текст
            return date_text
            
        except Exception as e:
            self.logger.debug(f"Ошибка конвертации даты '{date_text}': {e}")
            return date_text

    def save_reviews_to_csv(self, reviews: List[Dict], filename: str):
        """Обновление отзывов в CSV (перезапись файла)"""
        if not reviews:
            self.logger.warning("Нет отзывов для сохранения")
            return
        
        try:
            fieldnames = ['id', 'text', 'rating', 'author', 'date', 'source']
            
            # Удаляем старый CSV файл если существует
            if os.path.exists(filename):
                os.remove(filename)
                self.logger.info(f"🗑️ Удален старый CSV файл: {filename}")
            
            # Создаем новый CSV файл с актуальными данными
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(reviews)
            
            self.logger.info(f"💾 Обновлен CSV файл: {filename} ({len(reviews)} отзывов)")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления CSV: {e}")


