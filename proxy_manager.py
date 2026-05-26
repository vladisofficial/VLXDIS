#!/usr/bin/env python3
# proxy_manager.py
# VLXDIS - Менеджер прокси
# Telegram: @Itz_Vladis
# Build: 25.05.2026

import os
import random
from typing import Dict, List, Optional

class ProxyManager:
    """Управление пулом прокси."""
    
    def __init__(self, proxy_file: str = "socks5_proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies: List[Dict] = []
        self.load_from_file(proxy_file)
    
    def load_from_file(self, filepath: str) -> int:
        self.proxies = []
        if not os.path.exists(filepath):
            return 0
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    self._parse_proxy_line(line)
        return len(self.proxies)
    
    def _parse_proxy_line(self, line: str):
        parts = line.split(':')
        if len(parts) == 2:
            self.proxies.append({
                "scheme": "socks5",
                "hostname": parts[0],
                "port": int(parts[1])
            })
        elif len(parts) == 4:
            self.proxies.append({
                "scheme": "socks5",
                "hostname": parts[0],
                "port": int(parts[1]),
                "username": parts[2],
                "password": parts[3]
            })
    
    def add_proxy(self, proxy_str: str) -> bool:
        self._parse_proxy_line(proxy_str)
        return True
    
    def clear_proxies(self):
        self.proxies = []
    
    async def check_all_proxies(self) -> int:
        """Проверка работоспособности всех прокси."""
        import aiohttp
        from aiohttp_socks import ProxyConnector
        
        valid = 0
        test_url = "https://api.telegram.org"
        
        for proxy in self.proxies:
            try:
                if proxy.get('username'):
                    proxy_url = f"socks5://{proxy.get('username')}:{proxy.get('password')}@{proxy.get('hostname')}:{proxy.get('port')}"
                else:
                    proxy_url = f"socks5://{proxy.get('hostname')}:{proxy.get('port')}"
                
                connector = ProxyConnector.from_url(proxy_url)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            valid += 1
                            print(f"[VLXDIS] Прокси {proxy.get('hostname')}:{proxy.get('port')} - OK")
            except Exception as e:
                print(f"[VLXDIS] Прокси {proxy.get('hostname')}:{proxy.get('port')} - ОШИБКА: {e}")
        
        return valid
    
    def get_random_proxy(self) -> Optional[Dict]:
        if self.proxies:
            return random.choice(self.proxies)
        return None