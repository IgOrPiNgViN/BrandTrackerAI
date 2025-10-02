#!/usr/bin/env python3
"""
Тестирование API парсера отзывов
"""

import requests
import json

# URL API сервера
API_URL = "http://localhost:8000"

def test_health():
    """Тест проверки здоровья сервиса"""
    print("🔍 Тестирование health check...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_parse_yandex():
    """Тест парсинга Yandex"""
    print("\n🔍 Тестирование парсинга Yandex...")
    
    data = {
        "url": "https://yandex.ru/maps/org/galki/115736401897/reviews/",
        "review_amount": 10
    }
    
    try:
        response = requests.post(f"{API_URL}/parse", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Message: {result['message']}")
            print(f"Reviews count: {result['reviews_count']}")
            print(f"CSV preview (first 200 chars): {result['csv_data'][:200]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_parse_2gis():
    """Тест парсинга 2ГИС"""
    print("\n🔍 Тестирование парсинга 2ГИС...")
    
    data = {
        "url": "https://2gis.ru/moscow/search/Галки/firm/70000001040039867/37.60904%2C55.764912/tab/reviews",
        "review_amount": 5
    }
    
    try:
        response = requests.post(f"{API_URL}/parse", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Message: {result['message']}")
            print(f"Reviews count: {result['reviews_count']}")
            print(f"CSV preview (first 200 chars): {result['csv_data'][:200]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_parse_csv():
    """Тест получения CSV файла"""
    print("\n🔍 Тестирование получения CSV файла...")
    
    data = {
        "url": "https://yandex.ru/maps/org/galki/115736401897/reviews/",
        "review_amount": 5
    }
    
    try:
        response = requests.post(f"{API_URL}/parse/csv", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Disposition: {response.headers.get('content-disposition')}")
            print(f"CSV content preview (first 300 chars):")
            print(response.text[:300])
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_invalid_url():
    """Тест с неверным URL"""
    print("\n🔍 Тестирование с неверным URL...")
    
    data = {
        "url": "https://google.com",
        "review_amount": 5
    }
    
    try:
        response = requests.post(f"{API_URL}/parse", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования API парсера отзывов")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Parse Yandex", test_parse_yandex),
        ("Parse 2GIS", test_parse_2gis),
        ("Parse CSV", test_parse_csv),
        ("Invalid URL", test_invalid_url)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️ Некоторые тесты не пройдены")

if __name__ == "__main__":
    main()
