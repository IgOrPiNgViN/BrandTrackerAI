#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Анализатор тональности отзывов
"""

import re
from typing import Dict, List, Tuple
from collections import Counter

class SentimentAnalyzer:
    """Анализатор настроения отзывов"""
    
    def __init__(self):
        # Позитивные слова
        self.positive_words = {
            'отлично', 'прекрасно', 'замечательно', 'великолепно', 'супер',
            'хорошо', 'хороший', 'хорошая', 'хорошее', 'хорошие',
            'нравится', 'понравилось', 'понравился', 'понравилась',
            'рекомендую', 'рекомендую', 'советую',
            'вкусно', 'вкусный', 'вкусная', 'вкусное', 'вкусные',
            'быстро', 'быстрый', 'быстрая', 'быстрое', 'быстрые',
            'вежливо', 'вежливый', 'вежливая', 'вежливое', 'вежливые',
            'чисто', 'чистый', 'чистая', 'чистое', 'чистые',
            'удобно', 'удобный', 'удобная', 'удобное', 'удобные',
            'комфортно', 'комфортный', 'комфортная', 'комфортное',
            'люблю', 'обожаю', 'восхищаюсь',
            'лучший', 'лучшая', 'лучшее', 'лучшие',
            'отличный', 'отличная', 'отличное', 'отличные',
            'замечательный', 'замечательная', 'замечательное',
            'прекрасный', 'прекрасная', 'прекрасное',
            'восхитительный', 'восхитительная', 'восхитительное',
            'потрясающий', 'потрясающая', 'потрясающее',
            'шикарно', 'шикарный', 'шикарная', 'шикарное',
            'классно', 'классный', 'классная', 'классное',
            'круто', 'крутой', 'крутая', 'крутое',
            'топ', 'топовый', 'топовая', 'топовое',
            '5', 'пять', 'пятерка', 'пятерочка'
        }
        
        # Негативные слова
        self.negative_words = {
            'плохо', 'плохой', 'плохая', 'плохое', 'плохие',
            'ужасно', 'ужасный', 'ужасная', 'ужасное', 'ужасные',
            'отвратительно', 'отвратительный', 'отвратительная', 'отвратительное',
            'не нравится', 'не понравилось', 'не понравился', 'не понравилась',
            'не рекомендую', 'не советую',
            'не вкусно', 'невкусно', 'невкусный', 'невкусная', 'невкусное',
            'медленно', 'медленный', 'медленная', 'медленное', 'медленные',
            'грубо', 'грубый', 'грубая', 'грубое', 'грубые',
            'грязно', 'грязный', 'грязная', 'грязное', 'грязные',
            'неудобно', 'неудобный', 'неудобная', 'неудобное',
            'некомфортно', 'некомфортный', 'некомфортная',
            'ненавижу', 'терпеть не могу',
            'худший', 'худшая', 'худшее', 'худшие',
            'ужасный', 'ужасная', 'ужасное', 'ужасные',
            'кошмар', 'кошмарный', 'кошмарная', 'кошмарное',
            'ужас', 'ужасный', 'ужасная', 'ужасное',
            'разочарован', 'разочарована', 'разочаровано', 'разочарованы',
            'жалко', 'жаль',
            'проблема', 'проблемы', 'проблемный', 'проблемная',
            'жалоба', 'жалобы', 'жалуюсь',
            'недоволен', 'недовольна', 'недовольно', 'недовольны',
            '1', 'один', 'единица', 'единичка',
            '2', 'два', 'двойка',
            'долго', 'долгий', 'долгая', 'долгое',
            'дорого', 'дорогой', 'дорогая', 'дорогое',
            'обманули', 'обманул', 'обманула',
            'не работает', 'не работал', 'не работала',
            'сломалось', 'сломался', 'сломалась',
            'не приехал', 'не приехала', 'не приехало',
            'не привезли', 'не привезла', 'не привезло'
        }
        
        # Усилители (усиливают эмоцию)
        self.intensifiers = {
            'очень', 'очень', 'крайне', 'чрезвычайно', 'невероятно',
            'абсолютно', 'совершенно', 'полностью', 'вполне',
            'совсем', 'вовсе', 'вообще', 'совершенно',
            'особенно', 'исключительно', 'необычайно'
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """
        Анализирует тональность текста
        
        Args:
            text: Текст отзыва
        
        Returns:
            Dict с результатами анализа
        """
        if not text or not isinstance(text, str):
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'positive_count': 0,
                'negative_count': 0
            }
        
        text_lower = text.lower()
        
        # Подсчет позитивных и негативных слов
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # Подсчет усилителей
        intensifier_count = sum(1 for word in self.intensifiers if word in text_lower)
        
        # Определение тональности
        total_words = positive_count + negative_count
        if total_words == 0:
            sentiment = 'neutral'
            score = 0.0
        elif positive_count > negative_count:
            sentiment = 'positive'
            score = (positive_count - negative_count) / max(total_words, 1)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = -(negative_count - positive_count) / max(total_words, 1)
        else:
            sentiment = 'neutral'
            score = 0.0
        
        # Усиление оценки при наличии усилителей
        if intensifier_count > 0:
            score *= (1 + intensifier_count * 0.2)
            score = max(-1.0, min(1.0, score))  # Ограничение от -1 до 1
        
        # Уверенность (на основе количества найденных слов)
        confidence = min(1.0, total_words / 10.0)
        
        return {
            'sentiment': sentiment,
            'score': round(score, 3),
            'confidence': round(confidence, 3),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'intensifier_count': intensifier_count
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, any]]:
        """
        Анализирует список текстов
        
        Args:
            texts: Список текстов отзывов
        
        Returns:
            Список результатов анализа
        """
        return [self.analyze_sentiment(text) for text in texts]
    
    def get_sentiment_statistics(self, results: List[Dict[str, any]]) -> Dict[str, any]:
        """
        Получает статистику по тональности
        
        Args:
            results: Список результатов анализа
        
        Returns:
            Статистика
        """
        if not results:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'average_score': 0.0
            }
        
        sentiment_counts = Counter(r['sentiment'] for r in results)
        total = len(results)
        avg_score = sum(r['score'] for r in results) / total
        
        return {
            'total': total,
            'positive': sentiment_counts.get('positive', 0),
            'negative': sentiment_counts.get('negative', 0),
            'neutral': sentiment_counts.get('neutral', 0),
            'positive_percent': round(sentiment_counts.get('positive', 0) / total * 100, 1),
            'negative_percent': round(sentiment_counts.get('negative', 0) / total * 100, 1),
            'neutral_percent': round(sentiment_counts.get('neutral', 0) / total * 100, 1),
            'average_score': round(avg_score, 3)
        }
