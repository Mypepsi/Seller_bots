import re

data = {
    "http": "http://1:1@51.89.93.2:10345",
    "https": "http://1:1@51.89.93.2:10345"
}

http_value = data.get("http", "")  # Отримуємо значення для ключа "http"

# Використовуємо регулярний вираз для пошуку підрядка
match = re.search(r'://([^:]+):([^@]+)@([^:]+):(\d+)', http_value)

if match:
    fourth_value = match.group(4)  # Четверте значення після третього від ":"
    print(match.group(1))  # Виведе "10345"
    print(match.group(2))  # Виведе "10345"
    print(match.group(3))  # Виведе "10345"
    print(match.group(5))  # Виведе "10345"
else:
    print("Не вдалося знайти потрібний підрядок")
