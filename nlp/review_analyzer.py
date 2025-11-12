#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Комплексный анализатор отзывов
Объединяет анализ тональности и извлечение проблем
"""

import pandas as pd
from typing import Dict, List, Optional
from .sentiment_analyzer import SentimentAnalyzer
from .problem_extractor import ProblemExtractor

class ReviewAnalyzer:
    """Комплексный анализатор отзывов"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.problem_extractor = ProblemExtractor()
    
    def analyze_review(self, text: str, rating: Optional[int] = None) -> Dict[str, any]:
        """
        Анализирует один отзыв
        
        Args:
            text: Текст отзыва
            rating: Рейтинг (опционально)
        
        Returns:
            Полный анализ отзыва
        """
        sentiment = self.sentiment_analyzer.analyze_sentiment(text)
        problems = self.problem_extractor.extract_problems(text)
        
        result = {
            'text': text,
            'rating': rating,
            'sentiment': sentiment['sentiment'],
            'sentiment_score': sentiment['score'],
            'sentiment_confidence': sentiment['confidence'],
            'has_problems': len(problems) > 0,
            'problems_count': len(problems),
            'problems': problems,
            'problem_categories': [p['category'] for p in problems]
        }
        
        # Проверка согласованности рейтинга и тональности
        if rating is not None:
            if rating >= 4 and sentiment['sentiment'] == 'negative':
                result['rating_sentiment_mismatch'] = True
            elif rating <= 2 and sentiment['sentiment'] == 'positive':
                result['rating_sentiment_mismatch'] = True
            else:
                result['rating_sentiment_mismatch'] = False
        
        return result
    
    def analyze_dataframe(self, df: pd.DataFrame, 
                         text_column: str = 'text',
                         rating_column: Optional[str] = None) -> pd.DataFrame:
        """
        Анализирует DataFrame с отзывами
        
        Args:
            df: DataFrame с отзывами
            text_column: Название колонки с текстом
            rating_column: Название колонки с рейтингом (опционально)
        
        Returns:
            DataFrame с результатами анализа
        """
        results = []
        
        for idx, row in df.iterrows():
            text = row.get(text_column, '')
            rating = row.get(rating_column) if rating_column else None
            
            analysis = self.analyze_review(text, rating)
            analysis['original_index'] = idx
            results.append(analysis)
        
        return pd.DataFrame(results)
    
    def get_summary_statistics(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Получает сводную статистику по анализу
        
        Args:
            df: DataFrame с результатами анализа
        
        Returns:
            Сводная статистика
        """
        if df.empty:
            return {}
        
        # Статистика по тональности
        sentiment_stats = df['sentiment'].value_counts().to_dict()
        avg_sentiment_score = df['sentiment_score'].mean()
        
        # Статистика по проблемам
        total_reviews = len(df)
        reviews_with_problems = df['has_problems'].sum()
        total_problems = df['problems_count'].sum()
        
        # Топ категорий проблем
        all_categories = []
        for categories in df['problem_categories']:
            all_categories.extend(categories)
        
        from collections import Counter
        top_problem_categories = Counter(all_categories).most_common(10)
        
        # Распределение по рейтингам (если есть)
        rating_stats = {}
        if 'rating' in df.columns:
            rating_stats = df['rating'].value_counts().to_dict()
        
        return {
            'total_reviews': total_reviews,
            'sentiment_distribution': sentiment_stats,
            'average_sentiment_score': round(avg_sentiment_score, 3),
            'reviews_with_problems': int(reviews_with_problems),
            'reviews_with_problems_percent': round(reviews_with_problems / total_reviews * 100, 1),
            'total_problems_found': int(total_problems),
            'average_problems_per_review': round(total_problems / total_reviews, 2),
            'top_problem_categories': [
                {'category': cat, 'count': count} 
                for cat, count in top_problem_categories
            ],
            'rating_distribution': rating_stats
        }
    
    def generate_report(self, df: pd.DataFrame, output_file: Optional[str] = None) -> str:
        """
        Генерирует текстовый отчет
        
        Args:
            df: DataFrame с результатами анализа
            output_file: Путь к файлу для сохранения (опционально)
        
        Returns:
            Текст отчета
        """
        stats = self.get_summary_statistics(df)
        
        report = []
        report.append("=" * 60)
        report.append("ОТЧЕТ ПО АНАЛИЗУ ОТЗЫВОВ")
        report.append("=" * 60)
        report.append("")
        
        report.append(f"Всего отзывов: {stats['total_reviews']}")
        report.append("")
        
        report.append("ТОНАЛЬНОСТЬ ОТЗЫВОВ:")
        report.append("-" * 40)
        sentiment_dist = stats['sentiment_distribution']
        total = stats['total_reviews']
        
        for sentiment, count in sentiment_dist.items():
            percent = round(count / total * 100, 1)
            sentiment_ru = {
                'positive': 'Позитивные',
                'negative': 'Негативные',
                'neutral': 'Нейтральные'
            }.get(sentiment, sentiment)
            report.append(f"  {sentiment_ru}: {count} ({percent}%)")
        
        report.append(f"Средний балл тональности: {stats['average_sentiment_score']}")
        report.append("")
        
        report.append("ПРОБЛЕМЫ И ЖАЛОБЫ:")
        report.append("-" * 40)
        report.append(f"Отзывов с проблемами: {stats['reviews_with_problems']} ({stats['reviews_with_problems_percent']}%)")
        report.append(f"Всего проблем найдено: {stats['total_problems_found']}")
        report.append(f"Среднее проблем на отзыв: {stats['average_problems_per_review']}")
        report.append("")
        
        if stats['top_problem_categories']:
            report.append("ТОП ПРОБЛЕМ:")
            report.append("-" * 40)
            for i, item in enumerate(stats['top_problem_categories'][:5], 1):
                report.append(f"  {i}. {item['category']}: {item['count']} упоминаний")
        
        report.append("")
        report.append("=" * 60)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text
