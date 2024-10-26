
import pyotp

# Використовуємо секретний ключ у форматі Base32
secret_key = "mbvgfm4kshdi4k64"

# Створюємо об'єкт TOTP для генерації кодів
totp = pyotp.TOTP(secret_key)
code = totp.now()

print("Ваш 2FA код:", code)