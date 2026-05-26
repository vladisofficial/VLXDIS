#!/usr/bin/env python3
# history_manager.py
# VLXDIS - Менеджер истории сносов
# Telegram: @Itz_Vladis
# Build: 26.05.2026

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

class HistoryManager:
    """Управление историей сносов."""
    
    def __init__(self, history_path: str = "history/snos_history.json"):
        self.history_path = history_path
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        if not os.path.exists(self.history_path):
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4)
    
    def add_snos_record(self, config: Dict[str, Any]) -> str:
        record_id = str(uuid.uuid4())[:8]
        
        record = {
            "id": record_id,
            "software": "VLXDIS",
            "version": "1.6.0",
            "telegram_contact": config.get("telegram_contact", "@Itz_Vladis"),
            "target": config.get("target", "unknown"),
            "timestamp": config.get("timestamp", datetime.now().isoformat()),
            "completion_time": None,
            "status": "PREPARING",
            "report_count": config.get("report_count", 0),
            "reports_sent": 0,
            "successful": 0,
            "failed": 0,
            "report_types": config.get("report_types", []),
            "report_message": config.get("report_message", ""),
            "concurrent_sessions": config.get("concurrent_sessions", 0),
            "delay_range": list(config.get("delay_range", (0.5, 2.0))),
            "duration_seconds": 0,
            "proxy_count": len(config.get("proxy_list", [])),
            "session_count": len(config.get("session_pool", [])),
            "config_snapshot": {k: v for k, v in config.items() 
                              if k not in ["proxy_list", "session_pool"]}
        }
        
        history = self.get_all_records()
        history.append(record)
        self._save_history(history)
        self._create_detailed_report(record_id, record)
        return record_id
    
    def update_snos_record(self, record_id: str, updates: Dict[str, Any]):
        history = self.get_all_records()
        for record in history:
            if record.get("id") == record_id:
                record.update(updates)
                break
        self._save_history(history)
    
    def mark_completed(self, record_id: str, stats: Dict[str, Any]):
        updates = {
            "status": "COMPLETED",
            "completion_time": datetime.now().isoformat(),
            **stats
        }
        self.update_snos_record(record_id, updates)
    
    def mark_failed(self, record_id: str, error: str):
        updates = {
            "status": "FAILED",
            "completion_time": datetime.now().isoformat(),
            "error": error
        }
        self.update_snos_record(record_id, updates)
    
    def get_all_records(self) -> List[Dict]:
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def get_record_by_id(self, record_id: str) -> Optional[Dict]:
        history = self.get_all_records()
        for record in history:
            if record.get("id") == record_id:
                return record
        return None
    
    def _save_history(self, history: List[Dict]):
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    
    def _create_detailed_report(self, record_id: str, record: Dict):
        report_dir = "history/reports"
        os.makedirs(report_dir, exist_ok=True)
        report_path = f"{report_dir}/report_{record_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=4, ensure_ascii=False)
    
    def export_history(self, export_path: Optional[str] = None) -> str:
        if not export_path:
            export_path = f"history/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        history = self.get_all_records()
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_records": len(history),
            "records": history
        }
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)
        return export_path
    
    def clear_history(self):
        self._save_history([])