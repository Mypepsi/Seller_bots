import websocket
import threading
import time
import json


# Функція для обробки отриманих повідомлень
def on_message(ws, message):
    print(f"Received: {message}")
    message = json.loads(message)
    print(message['name'])


# Функція для обробки пінгів
def send_ping(ws):
    while True:
        # Формуємо JSON-повідомлення для пінгу
        online_send = json.dumps({"name": "ping"})
        ws.send(online_send)  # Відправляємо пінг через send()
        print("Ping sent: ", online_send)
        time.sleep(3)  # Чекаємо 60 секунд

# Функція для обробки відкриття з'єднання
def on_open(ws):
    print("Connection opened")
    # Стартуємо окремий потік для пінгів
    ping_thread = threading.Thread(target=send_ping, args=(ws,))
    ping_thread.start()


# Функція для обробки помилок
def on_error(ws, error):
    print(f"Error: {error}")


# Функція для обробки закриття з'єднання
def on_close(ws, close_status_code, close_msg):
    print("Connection closed")


if __name__ == "__main__":
    # Створюємо WebSocket-з'єднання
    ws = websocket.WebSocketApp(
        'wss://wssex.waxpeer.com',  # Заміни на свій WebSocket URL
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close
    )

    # Запускаємо WebSocket клієнт
    ws.run_forever()