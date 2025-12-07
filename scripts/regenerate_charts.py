#!/usr/bin/env python3
"""
Скрипт для перегенерации всех графиков NLP-анализа.
Запускайте при изменении датасета.

Использование:
    py scripts/regenerate_charts.py
    py scripts/regenerate_charts.py --data data/all_reviews.csv
"""

import os
import sys
import argparse

# Добавляем корневую папку проекта
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# Настройка matplotlib
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'DejaVu Sans'


def setup_directories():
    """Создаёт папки для сохранения графиков"""
    images_dir = os.path.join(project_root, 'reports', 'images')
    os.makedirs(images_dir, exist_ok=True)
    return images_dir


def load_and_analyze_data(data_path: str):
    """Загружает данные и запускает NLP-анализ"""
    from nlp.review_analyzer import ReviewAnalyzer
    
    print(f"📂 Загрузка данных: {data_path}")
    df = pd.read_csv(data_path, encoding='utf-8-sig')
    print(f"   Загружено {len(df)} отзывов")
    
    print("⏳ Запуск NLP-анализа...")
    analyzer = ReviewAnalyzer()
    rating_col = 'rating' if 'rating' in df.columns else None
    df_analyzed = analyzer.analyze_dataframe(df, text_column='text', rating_column=rating_col)
    
    # Удаляем дублирующиеся колонки
    if 'text' in df_analyzed.columns:
        df_analyzed = df_analyzed.drop(columns=['text'])
    if 'rating' in df_analyzed.columns:
        df_analyzed = df_analyzed.drop(columns=['rating'])
    
    # Объединяем результаты
    df = df.reset_index()
    df = df.merge(df_analyzed, left_on='index', right_on='original_index', how='left')
    df = df.drop(columns=['index', 'original_index'])
    
    print("✅ NLP-анализ завершён!")
    return df


def generate_chart_01_sentiment(df, images_dir):
    """График 1: Распределение тональности"""
    print("📊 Генерация: nlp_01_sentiment_distribution.png")
    
    sentiment_counts = df['sentiment'].value_counts()
    sentiment_labels = {'positive': 'Позитивные', 'negative': 'Негативные', 'neutral': 'Нейтральные'}
    sentiment_counts_ru = pd.Series({sentiment_labels.get(k, k): v for k, v in sentiment_counts.items()})
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    colors = ['#2ecc71', '#e74c3c', '#95a5a6']
    
    ax1.pie(sentiment_counts_ru.values, labels=sentiment_counts_ru.index, autopct='%1.1f%%', colors=colors, startangle=90)
    ax1.set_title('Распределение тональности отзывов', fontsize=14, fontweight='bold')
    
    bars = ax2.bar(sentiment_counts_ru.index, sentiment_counts_ru.values, color=colors)
    ax2.set_title('Количество отзывов по тональности', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Количество отзывов')
    ax2.set_xlabel('Тональность')
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_01_sentiment_distribution.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_02_problems(df, images_dir):
    """График 2: Анализ проблем"""
    print("📊 Генерация: nlp_02_problems_analysis.png")
    
    all_categories = []
    for categories in df['problem_categories']:
        try:
            if categories is None:
                continue
            if isinstance(categories, (list, tuple)) and len(categories) > 0:
                all_categories.extend([c for c in categories if c])
            elif isinstance(categories, str) and categories.strip():
                all_categories.extend([c.strip() for c in categories.split(',') if c.strip()])
        except:
            continue
    
    category_counts = Counter(all_categories)
    category_translation = {
        'качество_еды': 'Качество еды', 'обслуживание': 'Обслуживание',
        'чистота': 'Чистота', 'цены': 'Цены', 'ожидание': 'Ожидание',
        'атмосфера': 'Атмосфера', 'технические': 'Технические', 'размер_порций': 'Размер порций'
    }
    category_counts_ru = {category_translation.get(k, k): v for k, v in category_counts.items()}
    
    if category_counts_ru:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        top_categories = dict(sorted(category_counts_ru.items(), key=lambda x: x[1], reverse=True)[:10])
        
        y_pos = np.arange(len(top_categories))
        ax1.barh(y_pos, list(top_categories.values()), color='#e74c3c')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(list(top_categories.keys()))
        ax1.set_xlabel('Количество упоминаний')
        ax1.set_title('Топ проблем в отзывах', fontsize=14, fontweight='bold')
        ax1.invert_yaxis()
        
        ax2.pie(top_categories.values(), labels=top_categories.keys(), autopct='%1.1f%%', startangle=90)
        ax2.set_title('Распределение проблем', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{images_dir}/nlp_02_problems_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()


def generate_chart_03_scores(df, images_dir):
    """График 3: Распределение оценок тональности"""
    print("📊 Генерация: nlp_03_sentiment_scores.png")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(df['sentiment_score'], bins=30, color='#3498db', edgecolor='black', alpha=0.7)
    ax.axvline(df['sentiment_score'].mean(), color='red', linestyle='--', linewidth=2, 
               label=f'Среднее: {df["sentiment_score"].mean():.2f}')
    ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.3)
    ax.set_title('Распределение оценок тональности', fontsize=14, fontweight='bold')
    ax.set_xlabel('Оценка тональности (от -1 до +1)')
    ax.set_ylabel('Количество отзывов')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_03_sentiment_scores.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_04_link(df, images_dir):
    """График 4: Связь тональности и проблем"""
    print("📊 Генерация: nlp_04_sentiment_problems_link.png")
    
    sentiment_labels = {'positive': 'Позитивные', 'negative': 'Негативные', 'neutral': 'Нейтральные'}
    
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_data = pd.crosstab(df['sentiment'], df['has_problems'], normalize='index') * 100
    pivot_data.index = [sentiment_labels.get(idx, idx) for idx in pivot_data.index]
    pivot_data.columns = ['Без проблем', 'С проблемами']
    
    pivot_data.plot(kind='bar', ax=ax, color=['#2ecc71', '#e74c3c'], width=0.8)
    ax.set_title('Связь тональности и наличия проблем', fontsize=14, fontweight='bold')
    ax.set_xlabel('Тональность')
    ax.set_ylabel('Процент отзывов (%)')
    ax.legend(title='')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_04_sentiment_problems_link.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_05_rating(df, images_dir):
    """График 5: Анализ по рейтингам"""
    if 'rating' not in df.columns or not df['rating'].notna().any():
        print("⚠️  Пропуск nlp_05_rating_analysis.png (нет рейтингов)")
        return
    
    print("📊 Генерация: nlp_05_rating_analysis.png")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    rating_counts = df['rating'].value_counts().sort_index()
    ax1.bar(rating_counts.index, rating_counts.values, color='#f39c12', edgecolor='black')
    ax1.set_title('Распределение рейтингов', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Рейтинг')
    ax1.set_ylabel('Количество отзывов')
    
    rating_sentiment = pd.crosstab(df['rating'], df['sentiment'])
    rating_sentiment.plot(kind='bar', ax=ax2, color=['#e74c3c', '#95a5a6', '#2ecc71'])
    ax2.set_title('Тональность по рейтингам', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Рейтинг')
    ax2.set_ylabel('Количество отзывов')
    ax2.legend(['Негативные', 'Нейтральные', 'Позитивные'])
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=0)
    
    avg_sentiment_by_rating = df.groupby('rating')['sentiment_score'].mean()
    ax3.plot(avg_sentiment_by_rating.index, avg_sentiment_by_rating.values, marker='o', linewidth=2, markersize=8, color='#3498db')
    ax3.set_title('Средняя оценка тональности по рейтингам', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Рейтинг')
    ax3.set_ylabel('Средняя оценка тональности')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(0, color='black', linestyle='--', alpha=0.3)
    
    problems_by_rating = df.groupby('rating')['problems_count'].mean()
    ax4.bar(problems_by_rating.index, problems_by_rating.values, color='#e74c3c', edgecolor='black')
    ax4.set_title('Среднее количество проблем по рейтингам', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Рейтинг')
    ax4.set_ylabel('Среднее количество проблем')
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_05_rating_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_06_correlation(df, images_dir):
    """График 6: Корреляционная матрица"""
    print("📊 Генерация: nlp_06_correlation_matrix.png")
    
    corr_data = df.copy()
    sentiment_map = {'positive': 1, 'neutral': 0, 'negative': -1}
    corr_data['sentiment_numeric'] = corr_data['sentiment'].map(sentiment_map)
    
    numeric_cols = ['sentiment_score', 'sentiment_confidence', 'problems_count', 'has_problems', 'sentiment_numeric']
    if 'rating' in corr_data.columns:
        numeric_cols.append('rating')
    
    corr_matrix = corr_data[numeric_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0, square=True, linewidths=1, ax=ax)
    ax.set_title('Корреляционная матрица признаков', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_06_correlation_matrix.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_07_classification(df, images_dir):
    """График 7: Классификация"""
    print("📊 Генерация: nlp_07_classification.png")
    
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.metrics import confusion_matrix, accuracy_score
    from sklearn.preprocessing import StandardScaler
    
    X = df[['sentiment_score', 'sentiment_confidence']].copy()
    if 'rating' in df.columns:
        X['rating'] = df['rating'].fillna(df['rating'].median())
    X = X.fillna(X.mean())
    y = df['has_problems'].astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    }
    
    results = {}
    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        results[name] = {'accuracy': accuracy_score(y_test, y_pred), 'predictions': y_pred}
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, (name, result) in enumerate(results.items()):
        cm = confusion_matrix(y_test, result['predictions'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                    xticklabels=['Без проблем', 'С проблемами'],
                    yticklabels=['Без проблем', 'С проблемами'])
        axes[idx].set_title(f'{name}\nТочность: {result["accuracy"]:.3f}', fontweight='bold')
        axes[idx].set_ylabel('Истинные значения')
        axes[idx].set_xlabel('Предсказанные значения')
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_07_classification.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_08_clustering(df, images_dir):
    """График 8: Кластеризация"""
    print("📊 Генерация: nlp_08_clustering.png")
    
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    
    X_cluster = df[['sentiment_score', 'sentiment_confidence', 'problems_count']].copy()
    X_cluster = X_cluster.fillna(X_cluster.mean())
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_cluster)
    
    silhouette_scores = []
    K_range = range(2, 11)
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        silhouette_scores.append(silhouette_score(X_scaled, labels))
    
    optimal_k = K_range[np.argmax(silhouette_scores)]
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    scatter = axes[0].scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis', alpha=0.6, s=50)
    axes[0].set_title('Кластеризация отзывов (PCA)', fontweight='bold')
    axes[0].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)')
    axes[0].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)')
    plt.colorbar(scatter, ax=axes[0], label='Кластер')
    
    axes[1].plot(K_range, silhouette_scores, marker='o', linewidth=2, markersize=8)
    axes[1].axvline(optimal_k, color='r', linestyle='--', label=f'Оптимальное k={optimal_k}')
    axes[1].set_title('Поиск оптимального числа кластеров', fontweight='bold')
    axes[1].set_xlabel('Число кластеров')
    axes[1].set_ylabel('Silhouette Score')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_08_clustering.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_09_ensemble(df, images_dir):
    """График 9: Ансамблевое обучение"""
    print("📊 Генерация: nlp_09_ensemble_learning.png")
    
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier, BaggingClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    
    X = df[['sentiment_score', 'sentiment_confidence']].copy()
    if 'rating' in df.columns:
        X['rating'] = df['rating'].fillna(df['rating'].median())
    X = X.fillna(X.mean())
    y = df['has_problems'].astype(int)
    
    base_estimator = DecisionTreeClassifier(max_depth=5, random_state=42)
    
    ensemble_models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10),
        'Bagging': BaggingClassifier(estimator=base_estimator, n_estimators=50, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5),
        'AdaBoost': AdaBoostClassifier(estimator=base_estimator, n_estimators=50, random_state=42)
    }
    
    results_ensemble = {}
    for name, model in ensemble_models.items():
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
        model.fit(X, y)
        y_pred = model.predict(X)
        results_ensemble[name] = {
            'cv_mean': cv_scores.mean(), 'cv_std': cv_scores.std(),
            'accuracy': accuracy_score(y, y_pred), 'precision': precision_score(y, y_pred),
            'recall': recall_score(y, y_pred), 'f1': f1_score(y, y_pred)
        }
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    names = list(results_ensemble.keys())
    cv_means = [results_ensemble[n]['cv_mean'] for n in names]
    cv_stds = [results_ensemble[n]['cv_std'] for n in names]
    
    axes[0, 0].barh(names, cv_means, xerr=cv_stds, capsize=5)
    axes[0, 0].set_title('Точность (Cross-Validation)', fontweight='bold')
    axes[0, 0].set_xlabel('Точность')
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    x = np.arange(len(names))
    width = 0.2
    for i, metric in enumerate(metrics):
        values = [results_ensemble[n][metric] for n in names]
        axes[0, 1].bar(x + i*width, values, width, label=metric.capitalize())
    axes[0, 1].set_title('Метрики классификации', fontweight='bold')
    axes[0, 1].set_xticks(x + width * 1.5)
    axes[0, 1].set_xticklabels(names, rotation=45, ha='right')
    axes[0, 1].legend()
    
    comparison_df = pd.DataFrame(results_ensemble).T[['cv_mean', 'accuracy', 'precision', 'recall', 'f1']]
    sns.heatmap(comparison_df, annot=True, fmt='.3f', cmap='YlOrRd', ax=axes[1, 0])
    axes[1, 0].set_title('Сравнение всех метрик', fontweight='bold')
    
    best_model = max(results_ensemble.items(), key=lambda x: x[1]['cv_mean'])
    axes[1, 1].text(0.5, 0.5, f'🏆 Лучшая модель:\n{best_model[0]}\n\nТочность: {best_model[1]["cv_mean"]:.3f}',
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_09_ensemble_learning.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_10_association(df, images_dir):
    """График 10: Ассоциативные правила"""
    try:
        from mlxtend.frequent_patterns import apriori, association_rules
        from mlxtend.preprocessing import TransactionEncoder
    except ImportError:
        print("⚠️  Пропуск nlp_10_association_rules.png (требуется mlxtend)")
        return
    
    print("📊 Генерация: nlp_10_association_rules.png")
    
    transactions = []
    for categories in df['problem_categories']:
        transaction = []
        try:
            if categories is None:
                transactions.append([])
                continue
            if isinstance(categories, (list, tuple)):
                transaction = [c for c in categories if c]
            elif isinstance(categories, str):
                transaction = [c.strip() for c in categories.split(',') if c.strip()]
        except:
            transaction = []
        transactions.append(transaction)
    
    transactions_filtered = [t for t in transactions if len(t) > 0]
    
    if len(transactions_filtered) < 10:
        print("⚠️  Недостаточно данных для ассоциативных правил")
        return
    
    te = TransactionEncoder()
    te_ary = te.fit(transactions_filtered).transform(transactions_filtered)
    df_transactions = pd.DataFrame(te_ary, columns=te.columns_)
    
    frequent_itemsets = apriori(df_transactions, min_support=0.02, use_colnames=True)
    
    if len(frequent_itemsets) == 0:
        print("⚠️  Не найдено частых наборов")
        return
    
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.3)
    
    if len(rules) == 0:
        print("⚠️  Не найдено ассоциативных правил")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].scatter(rules['support'], rules['confidence'], s=rules['lift']*50, alpha=0.6, c=rules['lift'], cmap='viridis')
    axes[0].set_xlabel('Support')
    axes[0].set_ylabel('Confidence')
    axes[0].set_title('Ассоциативные правила\n(размер = lift)', fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    top_rules = rules.nlargest(10, 'lift')
    y_pos = np.arange(len(top_rules))
    axes[1].barh(y_pos, top_rules['lift'], color='#3498db')
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels([f"{', '.join(list(r['antecedents']))} → {', '.join(list(r['consequents']))}" 
                             for _, r in top_rules.iterrows()], fontsize=8)
    axes[1].set_xlabel('Lift')
    axes[1].set_title('Топ-10 правил по Lift', fontweight='bold')
    axes[1].invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_10_association_rules.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def generate_chart_11_forecast(df, images_dir):
    """График 11: Прогнозирование"""
    if 'date' not in df.columns:
        print("⚠️  Пропуск nlp_11_forecast.png (нет дат)")
        return
    
    print("📊 Генерация: nlp_11_forecast.png")
    
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
    df_copy = df_copy.dropna(subset=['date'])
    
    if len(df_copy) < 10:
        print("⚠️  Недостаточно данных для прогнозирования")
        return
    
    df_copy['year_month'] = df_copy['date'].dt.to_period('M')
    monthly_stats = df_copy.groupby('year_month').agg({
        'sentiment_score': 'mean', 'problems_count': 'mean', 'has_problems': 'mean'
    }).reset_index()
    monthly_stats['month_index'] = range(len(monthly_stats))
    
    future_months = 12
    X = monthly_stats[['month_index']].values
    
    predictions = {}
    for metric_name, col in [('Тональность', 'sentiment_score'), ('Проблемы', 'problems_count')]:
        y_data = monthly_stats[col].values
        lr = LinearRegression()
        lr.fit(X, y_data)
        future_indices = np.array(range(len(monthly_stats), len(monthly_stats) + future_months)).reshape(-1, 1)
        predictions[metric_name] = {'linear': lr.predict(future_indices), 'actual': y_data}
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    last_date = monthly_stats['year_month'].iloc[-1]
    future_dates = [str(last_date + i) for i in range(1, future_months + 1)]
    
    for idx, (metric_name, ylabel, ax) in enumerate([('Тональность', 'Средняя тональность', axes[0]), 
                                                       ('Проблемы', 'Среднее кол-во проблем', axes[1])]):
        pred_data = predictions[metric_name]
        historical_indices = range(len(monthly_stats))
        ax.plot(historical_indices, pred_data['actual'], 'o-', label='Исторические данные', linewidth=2, color='blue')
        future_indices_plot = range(len(monthly_stats), len(monthly_stats) + future_months)
        ax.plot(future_indices_plot, pred_data['linear'], 's--', label='Линейный прогноз', linewidth=2, color='green')
        ax.axvline(len(monthly_stats) - 0.5, color='gray', linestyle=':', linewidth=2, alpha=0.5)
        ax.set_xlabel('Период (месяцы)')
        ax.set_ylabel(ylabel)
        ax.set_title(f'Прогноз {metric_name.lower()} на следующие 12 месяцев', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{images_dir}/nlp_11_forecast.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Перегенерация графиков NLP-анализа')
    parser.add_argument('--data', type=str, default='data/all_reviews.csv', 
                        help='Путь к файлу данных (по умолчанию: data/all_reviews.csv)')
    args = parser.parse_args()
    
    data_path = os.path.join(project_root, args.data)
    
    print("=" * 60)
    print("🔄 ПЕРЕГЕНЕРАЦИЯ ГРАФИКОВ NLP-АНАЛИЗА")
    print("=" * 60)
    
    images_dir = setup_directories()
    print(f"📁 Папка для графиков: {images_dir}")
    
    df = load_and_analyze_data(data_path)
    
    print("\n📊 Генерация графиков...")
    
    generate_chart_01_sentiment(df, images_dir)
    generate_chart_02_problems(df, images_dir)
    generate_chart_03_scores(df, images_dir)
    generate_chart_04_link(df, images_dir)
    generate_chart_05_rating(df, images_dir)
    generate_chart_06_correlation(df, images_dir)
    generate_chart_07_classification(df, images_dir)
    generate_chart_08_clustering(df, images_dir)
    generate_chart_09_ensemble(df, images_dir)
    generate_chart_10_association(df, images_dir)
    generate_chart_11_forecast(df, images_dir)
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ ГРАФИКИ УСПЕШНО СГЕНЕРИРОВАНЫ!")
    print(f"📁 Сохранены в: {images_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()


