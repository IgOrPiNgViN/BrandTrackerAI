#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для анализа отзывов с помощью NLP
"""

import argparse
import sys
import os
import pandas as pd
from datetime import datetime
from nlp.review_analyzer import ReviewAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Анализ отзывов с помощью NLP')
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='Путь к CSV файлу с отзывами')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Путь для сохранения результатов (по умолчанию: input_analyzed.csv)')
    parser.add_argument('--report', '-r', type=str, default=None,
                       help='Путь для сохранения текстового отчета')
    parser.add_argument('--text-column', type=str, default='text',
                       help='Название колонки с текстом отзывов (по умолчанию: text)')
    parser.add_argument('--rating-column', type=str, default=None,
                       help='Название колонки с рейтингом (опционально)')
    
    args = parser.parse_args()
    
    # Проверка существования файла
    if not os.path.exists(args.input):
        print(f"❌ Ошибка: Файл {args.input} не найден!")
        sys.exit(1)
    
    print(f"📖 Загрузка данных из {args.input}...")
    
    try:
        # Загрузка данных
        df = pd.read_csv(args.input, encoding='utf-8-sig')
        print(f"✅ Загружено {len(df)} отзывов")
        
        # Проверка наличия колонки с текстом
        if args.text_column not in df.columns:
            print(f"❌ Ошибка: Колонка '{args.text_column}' не найдена!")
            print(f"Доступные колонки: {', '.join(df.columns)}")
            sys.exit(1)
        
        # Инициализация анализатора
        print("🔍 Инициализация NLP анализатора...")
        analyzer = ReviewAnalyzer()
        
        # Анализ отзывов
        print("📊 Начинаю анализ отзывов...")
        print("   Это может занять некоторое время...")
        
        analyzed_df = analyzer.analyze_dataframe(
            df, 
            text_column=args.text_column,
            rating_column=args.rating_column
        )
        
        print("✅ Анализ завершен!")
        
        # Сохранение результатов
        if args.output is None:
            base_name = os.path.splitext(args.input)[0]
            args.output = f"{base_name}_analyzed.csv"
        
        print(f"💾 Сохранение результатов в {args.output}...")
        
        # Подготовка данных для сохранения
        output_df = df.copy()
        output_df['sentiment'] = analyzed_df['sentiment']
        output_df['sentiment_score'] = analyzed_df['sentiment_score']
        output_df['sentiment_confidence'] = analyzed_df['sentiment_confidence']
        output_df['has_problems'] = analyzed_df['has_problems']
        output_df['problems_count'] = analyzed_df['problems_count']
        output_df['problem_categories'] = analyzed_df['problem_categories'].apply(
            lambda x: ', '.join(x) if x else ''
        )
        
        # Сохранение
        output_df.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"✅ Результаты сохранены в {args.output}")
        
        # Генерация отчета
        print("📄 Генерация отчета...")
        report = analyzer.generate_report(analyzed_df)
        
        if args.report is None:
            base_name = os.path.splitext(args.input)[0]
            args.report = f"{base_name}_report.txt"
        
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Отчет сохранен в {args.report}")
        print("")
        print("=" * 60)
        print(report)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
