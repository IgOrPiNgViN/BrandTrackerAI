#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования NLP анализа отзывов
"""

import sys
import os

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.review_analyzer import ReviewAnalyzer
import pandas as pd

def example_single_review():
    """Пример анализа одного отзыва"""
    print("=" * 60)
    print("ПРИМЕР 1: Анализ одного отзыва")
    print("=" * 60)
    
    analyzer = ReviewAnalyzer()
    
    # Примеры отзывов
    reviews = [
        {
            'text': 'Очень вкусная еда, быстро обслужили, рекомендую!',
            'rating': 5
        },
        {
            'text': 'Ужасное обслуживание, долго ждали, еда холодная. Не рекомендую.',
            'rating': 1
        },
        {
            'text': 'Нормально, ничего особенного. Цены немного завышены.',
            'rating': 3
        }
    ]
    
    for i, review in enumerate(reviews, 1):
        print(f"\nОтзыв {i}:")
        print(f"Текст: {review['text']}")
        print(f"Рейтинг: {review['rating']}")
        
        result = analyzer.analyze_review(review['text'], review['rating'])
        
        print(f"\nРезультаты анализа:")
        print(f"  Тональность: {result['sentiment']}")
        print(f"  Оценка: {result['sentiment_score']}")
        print(f"  Уверенность: {result['sentiment_confidence']}")
        print(f"  Есть проблемы: {result['has_problems']}")
        print(f"  Количество проблем: {result['problems_count']}")
        
        if result['problems']:
            print(f"  Категории проблем:")
            for problem in result['problems']:
                print(f"    - {problem['description']} ({problem['severity']})")
        
        print("-" * 60)

def example_batch_analysis():
    """Пример анализа нескольких отзывов"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 2: Анализ нескольких отзывов")
    print("=" * 60)
    
    # Создаем тестовый DataFrame
    data = {
        'text': [
            'Отличное место! Вкусная еда, вежливый персонал.',
            'Долго ждали заказ, еда была холодная. Обслуживание оставляет желать лучшего.',
            'Нормально, но цены завышены.',
            'Прекрасная атмосфера, рекомендую!',
            'Грязно, не убрали стол. Неприятный запах.'
        ],
        'rating': [5, 2, 3, 5, 1],
        'author': ['Иван', 'Мария', 'Петр', 'Анна', 'Сергей']
    }
    
    df = pd.DataFrame(data)
    
    analyzer = ReviewAnalyzer()
    analyzed_df = analyzer.analyze_dataframe(df, text_column='text', rating_column='rating')
    
    print(f"\nПроанализировано {len(analyzed_df)} отзывов\n")
    
    # Показываем результаты
    for idx, row in analyzed_df.iterrows():
        print(f"Отзыв {idx + 1}:")
        print(f"  Текст: {row['text'][:50]}...")
        print(f"  Тональность: {row['sentiment']} (оценка: {row['sentiment_score']})")
        print(f"  Проблемы: {row['problems_count']}")
        if row['problem_categories']:
            print(f"  Категории: {', '.join(row['problem_categories'])}")
        print()
    
    # Статистика
    stats = analyzer.get_summary_statistics(analyzed_df)
    
    print("=" * 60)
    print("СТАТИСТИКА:")
    print("=" * 60)
    print(f"Всего отзывов: {stats['total_reviews']}")
    print(f"\nТональность:")
    print(f"  Позитивные: {stats['sentiment_distribution'].get('positive', 0)}")
    print(f"  Негативные: {stats['sentiment_distribution'].get('negative', 0)}")
    print(f"  Нейтральные: {stats['sentiment_distribution'].get('neutral', 0)}")
    print(f"\nПроблемы:")
    print(f"  Отзывов с проблемами: {stats['reviews_with_problems']} ({stats['reviews_with_problems_percent']}%)")
    print(f"  Всего проблем: {stats['total_problems_found']}")
    print(f"  Среднее на отзыв: {stats['average_problems_per_review']}")
    
    if stats['top_problem_categories']:
        print(f"\nТоп проблем:")
        for item in stats['top_problem_categories'][:5]:
            print(f"  - {item['category']}: {item['count']}")

def example_report():
    """Пример генерации отчета"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 3: Генерация отчета")
    print("=" * 60)
    
    # Создаем тестовый DataFrame
    data = {
        'text': [
            'Отличное место! Вкусная еда, вежливый персонал.',
            'Долго ждали заказ, еда была холодная.',
            'Нормально, но цены завышены.',
            'Прекрасная атмосфера, рекомендую!',
            'Грязно, не убрали стол.'
        ],
        'rating': [5, 2, 3, 5, 1]
    }
    
    df = pd.DataFrame(data)
    
    analyzer = ReviewAnalyzer()
    analyzed_df = analyzer.analyze_dataframe(df, text_column='text', rating_column='rating')
    
    # Генерируем отчет
    report = analyzer.generate_report(analyzed_df)
    print("\n" + report)

if __name__ == "__main__":
    example_single_review()
    example_batch_analysis()
    example_report()
