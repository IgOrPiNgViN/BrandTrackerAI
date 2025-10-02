#!/usr/bin/env python3
"""
FastAPI сервер для парсинга отзывов
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, HttpUrl
from typing import Optional
import logging
import re
import os
import tempfile
from datetime import datetime
import sys

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.multi_page_yandex_parser import MultiPageYandexParser
from parsers.simple_twogis_parser import SimpleTwoGisParser

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('API')

app = FastAPI(
    title="Парсер отзывов API",
    description="API для парсинга отзывов с Yandex карт и 2ГИС",
    version="1.0.0"
)

class ParseRequest(BaseModel):
    """Модель запроса для парсинга"""
    url: str
    review_amount: int = 50

class ParseResponse(BaseModel):
    """Модель ответа"""
    success: bool
    message: str
    reviews_count: int
    csv_data: Optional[str] = None

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Парсер отзывов API",
        "version": "1.0.0",
        "endpoints": {
            "POST /parse": "Парсинг отзывов по URL",
            "GET /health": "Проверка здоровья сервиса"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/parse", response_model=ParseResponse)
async def parse_reviews(request: ParseRequest):
    """
    Парсинг отзывов по URL
    
    Args:
        request: Объект с URL и количеством отзывов
        
    Returns:
        CSV данные с отзывами
    """
    try:
        logger.info(f"Получен запрос на парсинг: {request.url}, количество: {request.review_amount}")
        
        # Валидация URL
        if not request.url:
            raise HTTPException(status_code=400, detail="URL не может быть пустым")
        
        if request.review_amount <= 0 or request.review_amount > 500:
            raise HTTPException(status_code=400, detail="Количество отзывов должно быть от 1 до 500")
        
        # Определяем тип парсера по URL
        if 'yandex.ru' in request.url:
            parser = MultiPageYandexParser()
            reviews = parser.parse_reviews_from_url(
                request.url, 
                limit=request.review_amount, 
                max_pages=5
            )
            source = "Yandex"
            
        elif '2gis.ru' in request.url:
            parser = SimpleTwoGisParser()
            reviews = parser.parse_reviews_from_url(
                request.url, 
                limit=request.review_amount
            )
            source = "2GIS"
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Неподдерживаемый URL. Поддерживаются только yandex.ru и 2gis.ru"
            )
        
        if not reviews:
            return ParseResponse(
                success=False,
                message="Отзывы не найдены",
                reviews_count=0
            )
        
        # Создаем CSV данные
        csv_data = _create_csv_data(reviews, source)
        
        logger.info(f"Успешно получено {len(reviews)} отзывов с {source}")
        
        return ParseResponse(
            success=True,
            message=f"Успешно получено {len(reviews)} отзывов с {source}",
            reviews_count=len(reviews),
            csv_data=csv_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.post("/parse/csv")
async def parse_reviews_csv(request: ParseRequest):
    """
    Парсинг отзывов с возвратом CSV файла
    
    Args:
        request: Объект с URL и количеством отзывов
        
    Returns:
        CSV файл
    """
    try:
        logger.info(f"Получен запрос на парсинг CSV: {request.url}, количество: {request.review_amount}")
        
        # Валидация URL
        if not request.url:
            raise HTTPException(status_code=400, detail="URL не может быть пустым")
        
        if request.review_amount <= 0 or request.review_amount > 500:
            raise HTTPException(status_code=400, detail="Количество отзывов должно быть от 1 до 500")
        
        # Определяем тип парсера по URL
        if 'yandex.ru' in request.url:
            parser = MultiPageYandexParser()
            reviews = parser.parse_reviews_from_url(
                request.url, 
                limit=request.review_amount, 
                max_pages=5
            )
            source = "Yandex"
            
        elif '2gis.ru' in request.url:
            parser = SimpleTwoGisParser()
            reviews = parser.parse_reviews_from_url(
                request.url, 
                limit=request.review_amount
            )
            source = "2GIS"
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Неподдерживаемый URL. Поддерживаются только yandex.ru и 2gis.ru"
            )
        
        if not reviews:
            raise HTTPException(status_code=404, detail="Отзывы не найдены")
        
        # Создаем CSV данные
        csv_data = _create_csv_data(reviews, source)
        
        # Создаем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reviews_{source.lower()}_{timestamp}.csv"
        
        logger.info(f"Успешно получено {len(reviews)} отзывов с {source}")
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

def _create_csv_data(reviews: list, source: str) -> str:
    """Создание CSV данных из списка отзывов"""
    import csv
    import io
    
    output = io.StringIO()
    fieldnames = ['id', 'text', 'rating', 'author', 'date', 'source', 'timestamp']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Записываем заголовки
    writer.writeheader()
    
    # Записываем отзывы
    for i, review in enumerate(reviews):
        writer.writerow({
            'id': f"{source.lower()}_{i:03d}",
            'text': review.get('text', ''),
            'rating': review.get('rating', 0),
            'author': review.get('author', ''),
            'date': review.get('date', ''),
            'source': source,
            'timestamp': datetime.now().isoformat()
        })
    
    return output.getvalue()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
