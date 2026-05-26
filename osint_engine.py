#!/usr/bin/env python3
# osint_engine.py
# VLXDIS OSINT Engine v1.6.0
# Build: 26.05.2026
# Telegram: @Itz_Vladis

import subprocess
import json
import os
import asyncio
from typing import Dict, List, Optional

class OSINTEngine:
    """Движок OSINT-поиска."""
    
    # API-ключи (замени на свои)
    LEAKCHECK_API_KEY = "YOUR_LEAKCHECK_API_KEY"
    
    @staticmethod
    def search_username(username: str) -> Dict:
        """Поиск username по соцсетям через Sherlock."""
        result = {
            "username": username,
            "found_sites": [],
            "errors": []
        }
        
        try:
            proc = subprocess.run(
                ["sherlock", username, "--print-found", "--timeout", "10",
                 "--site", "Telegram", "--site", "Instagram", "--site", "Twitter",
                 "--site", "Facebook", "--site", "VK", "--site", "YouTube",
                 "--site", "GitHub", "--site", "Reddit", "--site", "TikTok",
                 "--site", "Snapchat", "--site", "LinkedIn", "--site", "Pinterest",
                 "--site", "Twitch", "--site", "Steam", "--site", "Spotify",
                 "--site", "Discord", "--site", "Tumblr", "--site", "Medium",
                 "--no-color", "--timeout", "10"],
                capture_output=True, text=True, timeout=90
            )
            
            for line in proc.stdout.split('\n'):
                if '[+]' in line:
                    site = line.replace('[+]', '').strip().split(':')[0].strip()
                    if site:
                        result["found_sites"].append(site)
                        
        except subprocess.TimeoutExpired:
            result["errors"].append("Превышено время ожидания")
        except FileNotFoundError:
            result["errors"].append("Sherlock не установлен. pip install sherlock-project")
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    @staticmethod
    async def search_phone(phone: str, client=None) -> Dict:
        """Поиск информации по номеру телефона через Telegram."""
        result = {
            "phone": phone,
            "telegram_user": None,
            "errors": []
        }
        
        if client is None:
            result["errors"].append("Нет клиента Telegram")
            return result
        
        phone = phone.strip()
        if not phone.startswith('+'):
            phone = '+' + phone
        
        try:
            from pyrogram.raw import functions, types
            
            imported = await client.invoke(
                functions.contacts.ImportContacts(
                    contacts=[
                        types.InputPhoneContact(
                            client_id=42,
                            phone=phone,
                            first_name="",
                            last_name=""
                        )
                    ]
                )
            )
            
            if imported and imported.users:
                user = imported.users[0]
                result["telegram_user"] = {
                    "id": user.id,
                    "username": user.username or "нет",
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "phone": user.phone or phone,
                    "is_scam": user.scam if hasattr(user, 'scam') else False,
                    "is_premium": user.premium if hasattr(user, 'premium') else False,
                }
                
                try:
                    await client.invoke(
                        functions.contacts.DeleteContacts(id=[user.id])
                    )
                except:
                    pass
            else:
                result["errors"].append("Пользователь не найден")
                
        except Exception as e:
            result["errors"].append(f"Ошибка: {e}")
        
        return result
    
    @staticmethod
    async def search_id(user_id: int, client=None) -> Dict:
        """Поиск информации по ID через Telegram."""
        result = {
            "user_id": user_id,
            "user_info": None,
            "errors": []
        }
        
        if client is None:
            result["errors"].append("Нет клиента Telegram")
            return result
        
        try:
            user = await client.get_users(user_id)
            
            if user:
                result["user_info"] = {
                    "id": user.id,
                    "username": user.username or "нет",
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "phone": user.phone_number or "скрыт",
                    "is_scam": user.is_scam,
                    "is_premium": user.is_premium,
                    "is_verified": user.is_verified,
                    "is_bot": user.is_bot,
                }
            else:
                result["errors"].append("Пользователь не найден")
                
        except Exception as e:
            result["errors"].append(f"Ошибка: {e}")
        
        return result
    
    @staticmethod
    def search_email(email: str) -> Dict:
        """Поиск email в утечках через HaveIBeenPwned + BreachDirectory."""
        result = {
            "email": email,
            "breaches": [],
            "errors": []
        }
        
        try:
            import requests
            
            # Способ 1: HaveIBeenPwned
            try:
                resp = requests.get(
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                    headers={"User-Agent": "VLXDIS-OSINT", "hibp-api-key": ""},
                    timeout=15
                )
                
                if resp.status_code == 200:
                    for breach in resp.json():
                        result["breaches"].append({
                            "name": breach.get("Name", "Неизвестно"),
                            "date": breach.get("BreachDate", ""),
                            "data_classes": breach.get("DataClasses", [])
                        })
            except:
                pass
            
            # Способ 2: Бесплатный BreachDirectory
            if not result["breaches"]:
                try:
                    resp2 = requests.get(
                        f"https://breachdirectory.org/api?email={email}",
                        headers={"User-Agent": "VLXDIS-OSINT"},
                        timeout=15
                    )
                    
                    if resp2.status_code == 200:
                        data = resp2.json()
                        if data.get("breaches"):
                            for breach in data["breaches"]:
                                result["breaches"].append({
                                    "name": breach.get("name", "Неизвестно"),
                                    "date": breach.get("breach_date", ""),
                                    "data_classes": breach.get("data_classes", [])
                                })
                except:
                    pass
            
            if not result["breaches"]:
                result["errors"].append("Утечек не найдено")
                
        except Exception as e:
            result["errors"].append(f"Ошибка: {e}")
        
        return result
    
    @staticmethod
    def search_leakcheck(query: str, query_type: str = "email") -> Dict:
        """Поиск в слитых базах через LeakCheck Public API."""
        result = {
            "query": query,
            "results": [],
            "sources": [],
            "errors": []
        }
        
        try:
            import requests
            
            # LeakCheck Public API — GET запрос
            url = f"https://leakcheck.io/api/public?check={query}"
            
            resp = requests.get(url, timeout=30)
            
            if resp.status_code == 200:
                response_data = resp.json()
                
                if response_data.get("success"):
                    result["found"] = response_data.get("found", 0)
                    result["fields"] = response_data.get("fields", [])
                    
                    for source in response_data.get("sources", []):
                        result["sources"].append({
                            "name": source.get("name", "Неизвестно"),
                            "date": source.get("date", "")
                        })
                    
                    if not result["sources"]:
                        result["errors"].append("Ничего не найдено")
                else:
                    result["errors"].append(response_data.get("error", "Ошибка API"))
            elif resp.status_code == 404:
                result["errors"].append("Ничего не найдено")
            elif resp.status_code == 403:
                result["errors"].append("Доступ запрещён. Попробуйте через VPN.")
            elif resp.status_code == 429:
                result["errors"].append("Слишком много запросов. Подождите.")
            else:
                result["errors"].append(f"HTTP {resp.status_code}")
                
        except Exception as e:
            result["errors"].append(f"Ошибка: {e}")
        
        return result
    
    @staticmethod
    def search_full(username: str, phone: str = None, email: str = None) -> Dict:
        """Комплексный поиск: всё сразу."""
        result = {
            "username": None,
            "phone": None,
            "email": None,
            "errors": []
        }
        
        if username:
            result["username"] = OSINTEngine.search_username(username)
        
        if phone:
            result["phone"] = OSINTEngine.search_leakcheck(phone, "phone")
        
        if email:
            result["email"] = OSINTEngine.search_email(email)
        
        return result