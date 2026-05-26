#!/usr/bin/env python3
# session_manager.py
# VLXDIS - Менеджер сессий
# Telegram: @Itz_Vladis
# Build: 25.05.2026

import json
import os
import random
from typing import Dict, List, Optional
from datetime import datetime

class SessionManager:
    """Управление сессиями Telegram."""
    
    def __init__(self, cache_path: str = "sessions_cache.json"):
        self.cache_path = cache_path
        self._ensure_cache_file()
    
    def _ensure_cache_file(self):
        if not os.path.exists(self.cache_path):
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump({"sessions": []}, f, indent=4)
    
    def get_cached_sessions(self) -> List[Dict]:
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("sessions", [])
        except (json.JSONDecodeError, IOError):
            return []
    
    def load_from_file(self, filepath: str) -> int:
        if not os.path.exists(filepath):
            return 0
        loaded = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.add_session(line)
                    loaded += 1
        return loaded
    
    def add_session(self, session_string: str, phone: str = "") -> bool:
        cache = self.get_cached_sessions()
        for sess in cache:
            if sess.get("session_string") == session_string:
                return False
        cache.append({
            "phone": phone or f"session_{len(cache)+1}",
            "session_string": session_string,
            "added_at": datetime.now().isoformat(),
            "reports_sent": 0,
            "is_active": True
        })
        self._save_cache({"sessions": cache})
        return True
    
    def _save_cache(self, data: Dict):
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    async def create_session(self, phone: str) -> Optional[str]:
        """Создание новой сессии через Pyrogram."""
        try:
            from pyrogram import Client
            
            config = {}
            if os.path.exists("config.json"):
                with open("config.json", 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            api_id = config.get("api_id", 2040)
            api_hash = config.get("api_hash", "b18441a1ff607e10a989891a5462e627")
            
            client = Client(
                name=f"session_{phone.replace('+', '')}_{random.randint(1000, 9999)}",
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone,
                in_memory=True
            )
            
            await client.connect()
            
            sent_code = await client.send_code(phone)
            print(f"[VLXDIS] Код отправлен на {phone}")
            
            code = input(f"[VLXDIS] Введите код из Telegram/SMS: ").strip()
            
            try:
                await client.sign_in(phone, sent_code.phone_code_hash, code)
            except Exception as e:
                if "password" in str(e).lower():
                    password = input(f"[VLXDIS] Введите пароль 2FA: ").strip()
                    await client.check_password(password)
            
            session_string = await client.export_session_string()
            
            self.add_session(session_string, phone)
            
            with open("session_strings.txt", "a", encoding="utf-8") as f:
                f.write(session_string + "\n")
            
            print(f"[VLXDIS] Сессия создана и сохранена!")
            
            await client.disconnect()
            return session_string
            
        except Exception as e:
            print(f"[VLXDIS] Ошибка создания сессии: {e}")
            return None
    
    async def validate_all_sessions(self) -> int:
        """Проверка валидности всех сессий."""
        from pyrogram import Client
        
        config = {}
        if os.path.exists("config.json"):
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        api_id = config.get("api_id", 2040)
        api_hash = config.get("api_hash", "b18441a1ff607e10a989891a5462e627")
        
        sessions = self.get_cached_sessions()
        valid_count = 0
        
        for i, sess in enumerate(sessions):
            try:
                client = Client(
                    name=f"validate_{i}_{random.randint(1000, 9999)}",
                    session_string=sess.get("session_string"),
                    api_id=api_id,
                    api_hash=api_hash,
                    in_memory=True,
                    no_updates=True
                )
                await client.connect()
                me = await client.get_me()
                await client.disconnect()
                
                if me and me.id > 0:
                    valid_count += 1
                    print(f"[VLXDIS] Сессия {i+1} ({sess.get('phone', 'Unknown')}) - OK")
            except Exception as e:
                print(f"[VLXDIS] Сессия {i+1} ({sess.get('phone', 'Unknown')}) - ОШИБКА: {type(e).__name__}")
        
        return valid_count
    
    def export_to_file(self, filepath: str):
        sessions = self.get_cached_sessions()
        with open(filepath, 'w', encoding='utf-8') as f:
            for sess in sessions:
                f.write(sess.get("session_string", "") + "\n")