from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client.test  # Попробуйте подключиться к тестовой базе данных
    print("Подключение успешно!")
except Exception as e:
    print(f"Ошибка подключения: {e}")
