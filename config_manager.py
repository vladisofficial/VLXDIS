#!/usr/bin/env python3
# config_manager.py
# VLXDIS - Менеджер конфигурации
# Telegram: @Itz_Vladis
# Build: 26.05.2026

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

class ConfigManager:
    """
    Управление конфигурационными файлами.
    
    Формат config.json:
    {
        "api_id": 2040,
        "api_hash": "b18441a1ff607e10a989891a5462e627",
        "max_snos_time": 120,
        "auto_save": true,
        "logging": true,
        "version": "1.6.0"
    }
    """
    
    DEFAULT_CONFIG = {
        "api_id": 2040,
        "api_hash": "b18441a1ff607e10a989891a5462e627",
        "max_snos_time": 120,
        "auto_save": True,
        "logging": True,
        "version": "1.6.0",
        "build_date": "26.05.2026",
        "software": "VLXDIS",
        "telegram_contact": "@Itz_Vladis",
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat()
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
    
    def load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла."""
        if not os.path.exists(self.config_path):
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Объединяем с значениями по умолчанию
            merged_config = {**self.DEFAULT_CONFIG, **config}
            return merged_config
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Ошибка чтения конфига: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Создание конфигурации по умолчанию."""
        os.makedirs(os.path.dirname(self.config_path) if os.path.dirname(self.config_path) else ".", exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any], custom_path: Optional[str] = None) -> bool:
        """Сохранение конфигурации в файл."""
        save_path = custom_path or self.config_path
        
        # Обновляем временную метку
        config["last_modified"] = datetime.now().isoformat()
        
        try:
            # Создаем директорию если нужно
            save_dir = os.path.dirname(save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"[ERROR] Ошибка сохранения конфига: {e}")
            return False
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Обновление отдельной настройки."""
        config = self.load_config()
        config[key] = value
        return self.save_config(config)