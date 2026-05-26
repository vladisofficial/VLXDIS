from pyrogram import Client

session = "Вставь сюда свою строчку сессии"

app = Client(name="check", session_string=session, api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627", in_memory=True)

with app:
    me = app.get_me()
    print(f"OK: @{me.username} | ID: {me.id} | Phone: {me.phone_number}")