from pyrogram import Client

# Замени на свои данные
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

phone = input("Введите номер телефона (+79XXXXXXXXX): ")

app = Client(
    name=f"session_{phone.replace('+', '')}",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=phone,
    in_memory=True
)

with app:
    session_string = app.export_session_string()
    print("\n" + "=" * 50)
    print("СТРОКА СЕССИИ:")
    print(session_string)
    print("=" * 50)
    
    # Автоматически сохраняем в файл
    with open("session_strings.txt", "a", encoding="utf-8") as f:
        f.write(session_string + "\n")
    print("\n[✓] Сессия сохранена в session_strings.txt")