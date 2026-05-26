from pyrogram import Client
import os

# Путь к твоему файлу
SESSION_FILE = "Вставь сюда название файла pyrogram"

if not os.path.exists(SESSION_FILE):
    print(f"Файл {SESSION_FILE} не найден!")
    print("Перемести файл в папку V:\\VLXDIS_v1.6.0\\extract и запусти снова")
    input("Enter...")
    exit()

# Имя без .session
name = SESSION_FILE.replace(".session", "")

app = Client(
    name=name,
    api_id=2040,
    api_hash="b18441a1ff607e10a989891a5462e627"
)

with app:
    session_string = app.export_session_string()
    print("\n" + "=" * 50)
    print("СТРОКА СЕССИИ:")
    print(session_string)
    print("=" * 50)
    
    with open("session_strings.txt", "a", encoding="utf-8") as f:
        f.write(session_string + "\n")
    
    print("\n[OK] Сохранено в session_strings.txt")