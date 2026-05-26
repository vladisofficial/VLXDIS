#!/usr/bin/env python3
# report_engine.py
# VLXDIS - Полноценный движок массовых жалоб Telegram
# Telegram: @Itz_Vladis
# Build: 25.05.2026
# Версия: 1.6.0

import asyncio
import random
import time
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.raw.base import ReportReason
from pyrogram.errors import (
    FloodWait, PeerIdInvalid, UserDeactivatedBan, RPCError
)

class ReportEngine:
    """VLXDIS Report Engine - Полноценный движок отправки жалоб."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.target = config.get('target')
        self.report_types = config.get('report_types', ['inputReportReasonSpam'])
        self.report_count = int(config.get('report_count', 500))
        self.concurrent_sessions = int(config.get('concurrent_sessions', 50))
        self.report_message = config.get('report_message', 'This account violates Telegram Terms of Service.')
        
        delay_range = config.get('delay_range', (0.5, 2.0))
        self.delay_range = (float(delay_range[0]), float(delay_range[1]))
        
        self.session_pool = config.get('session_pool', [])
        self.proxy_list = config.get('proxy_list', [])
        self.telegram_contact = config.get('telegram_contact', '@Itz_Vladis')
        
        self.stats = {
            'total_sent': 0,
            'successful': 0,
            'failed': 0,
            'flood_limited': 0,
            'start_time': time.time(),
        }
        
        self._stats_lock = asyncio.Lock()
        
        self.api_id = config.get('api_id', 2040)
        self.api_hash = config.get('api_hash', 'b18441a1ff607e10a989891a5462e627')
        
        os.makedirs('logs', exist_ok=True)
        self.log_file = f"logs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def _log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except:
            pass
    
    def _get_random_proxy(self) -> Optional[Dict]:
        if not self.proxy_list:
            return None
        return random.choice(self.proxy_list)
    
    def _get_report_reason(self, reason_name: str) -> ReportReason:
        reason_map = {
            'inputReportReasonSpam': types.InputReportReasonSpam(),
            'inputReportReasonViolence': types.InputReportReasonViolence(),
            'inputReportReasonPornography': types.InputReportReasonPornography(),
            'inputReportReasonChildAbuse': types.InputReportReasonChildAbuse(),
            'inputReportReasonCopyright': types.InputReportReasonCopyright(),
            'inputReportReasonOther': types.InputReportReasonOther(),
        }
        return reason_map.get(reason_name, types.InputReportReasonOther())
    
    def _generate_message_variant(self, base_message: str) -> str:
        variants = [
            base_message,
            f"{base_message} Case #{random.randint(10000, 99999)}",
            f"URGENT: {base_message}",
        ]
        return random.choice(variants)
    
    async def _resolve_target_peer(self, client: Client):
        target = self.target.strip()
        
        # По username
        username = target.lstrip('@')
        if not target.isdigit() and not target.startswith('+'):
            try:
                peer = await client.resolve_peer(username)
                self._log(f"Цель найдена по username: @{username}")
                return peer
            except PeerIdInvalid:
                self._log(f"Username не найден: @{username}")
            except Exception as e:
                self._log(f"Ошибка username: {type(e).__name__}")
        
        # По номеру телефона
        is_phone = target.startswith('+') or (target.isdigit() and len(target) >= 10)
        if is_phone:
            phone = target if target.startswith('+') else f"+{target}"
            self._log(f"Ищу по номеру: {phone}")
            try:
                imported = await client.invoke(
                    functions.contacts.ImportContacts(
                        contacts=[
                            types.InputPhoneContact(
                                client_id=random.randint(10000, 99999),
                                phone=phone,
                                first_name="target",
                                last_name=""
                            )
                        ]
                    )
                )
                if imported and imported.users:
                    user = imported.users[0]
                    peer = types.InputPeerUser(user_id=user.id, access_hash=user.access_hash)
                    try:
                        await client.invoke(functions.contacts.DeleteContacts(id=[user.id]))
                    except:
                        pass
                    self._log(f"Цель найдена по номеру: {phone}")
                    return peer
                else:
                    self._log("Пользователь с таким номером не найден")
            except Exception as e:
                self._log(f"Ошибка номера: {type(e).__name__}")
        
        # По ID
        if target.isdigit():
            try:
                peer = await client.resolve_peer(int(target))
                self._log(f"Цель найдена по ID: {target}")
                return peer
            except:
                pass
        
        self._log(f"НЕ УДАЛОСЬ НАЙТИ ЦЕЛЬ: {target}", 'ERROR')
        return None
    
    async def _send_single_report(
        self, 
        session_string: str, 
        session_index: int,
        proxy: Optional[Dict] = None
    ) -> Dict[str, Any]:
        result = {
            'success': False,
            'error': None,
            'flood_wait': None,
            'session_index': session_index
        }
        
        client = None
        
        try:
            client = Client(
                name=f"vlxdis_{session_index}_{random.randint(10000, 99999)}",
                session_string=session_string,
                api_id=self.api_id,
                api_hash=self.api_hash,
                proxy=proxy,
                in_memory=True,
                no_updates=True
            )
            
            await client.connect()
            
            target_peer = await self._resolve_target_peer(client)
            if target_peer is None:
                result['error'] = 'Failed to resolve target peer'
                return result
            
            reason_name = random.choice(self.report_types)
            reason = self._get_report_reason(reason_name)
            message = self._generate_message_variant(self.report_message)
            
            await client.invoke(
                functions.account.ReportPeer(
                    peer=target_peer,
                    reason=reason,
                    message=message
                )
            )
            
            result['success'] = True
            
            async with self._stats_lock:
                self.stats['successful'] += 1
                self.stats['total_sent'] += 1
            
            self._log(f"Сессия #{session_index}: ЖАЛОБА ОТПРАВЛЕНА ({reason_name}) | {self.stats['total_sent']}/{self.report_count}", 'SUCCESS')
            
        except FloodWait as e:
            result['flood_wait'] = e.value
            async with self._stats_lock:
                self.stats['flood_limited'] += 1
                self.stats['total_sent'] += 1
            self._log(f"Сессия #{session_index}: FLOOD WAIT {e.value}с", 'WARNING')
            await asyncio.sleep(min(e.value, 60))
            
        except UserDeactivatedBan:
            result['error'] = 'Account deactivated'
            async with self._stats_lock:
                self.stats['failed'] += 1
                self.stats['total_sent'] += 1
            self._log(f"Сессия #{session_index}: АККАУНТ ЗАБАНЕН", 'ERROR')
            
        except PeerIdInvalid:
            result['error'] = 'Invalid peer'
            async with self._stats_lock:
                self.stats['failed'] += 1
                self.stats['total_sent'] += 1
            self._log(f"Сессия #{session_index}: ЦЕЛЬ НЕ НАЙДЕНА", 'ERROR')
            
        except Exception as e:
            result['error'] = f'{type(e).__name__}: {str(e)[:100]}'
            async with self._stats_lock:
                self.stats['failed'] += 1
                self.stats['total_sent'] += 1
            self._log(f"Сессия #{session_index}: ОШИБКА: {type(e).__name__}: {str(e)[:200]}", 'ERROR')
            
        finally:
            if client and client.is_connected:
                try:
                    await client.disconnect()
                except:
                    pass
        
        return result
    
    async def _session_worker(self, session_data: Dict, session_index: int, semaphore: asyncio.Semaphore):
        session_string = session_data.get('session_string')
        if not session_string:
            return
        
        proxy = session_data.get('proxy') or self._get_random_proxy()
        
        try:
            async with semaphore:
                consecutive_failures = 0
                max_failures = 3
                
                while self.stats['total_sent'] < self.report_count:
                    if consecutive_failures >= max_failures:
                        self._log(f"Сессия #{session_index}: Лимит неудач, остановка")
                        break
                    
                    delay = random.uniform(*self.delay_range)
                    await asyncio.sleep(delay)
                    
                    result = await self._send_single_report(
                        session_string=session_string,
                        session_index=session_index,
                        proxy=proxy
                    )
                    
                    if result['success']:
                        consecutive_failures = 0
                    elif result['flood_wait']:
                        consecutive_failures += 1
                        proxy = self._get_random_proxy()
                    else:
                        consecutive_failures += 1
                        if result['error'] and 'deactivated' in result['error'].lower():
                            break
                    
                    if self.stats['total_sent'] % random.randint(3, 7) == 0:
                        proxy = self._get_random_proxy()
        except Exception as e:
            self._log(f"Сессия #{session_index}: ОШИБКА ВОРКЕРА: {type(e).__name__}", 'ERROR')
    
    async def run_report_campaign(self):
        self._log("=" * 60)
        self._log("VLXDIS REPORT ENGINE - ЗАПУСК КАМПАНИИ")
        self._log("=" * 60)
        self._log(f"Цель: {self.target}")
        self._log(f"Запланировано жалоб: {self.report_count}")
        self._log(f"Доступно сессий: {len(self.session_pool)}")
        self._log(f"Доступно прокси: {len(self.proxy_list)}")
        self._log("=" * 60)
        
        if not self.session_pool:
            self._log("НЕТ СЕССИЙ", 'ERROR')
            return
        
        if not self.target:
            self._log("НЕТ ЦЕЛИ", 'ERROR')
            return
        
        active_sessions = self.session_pool[:min(len(self.session_pool), self.concurrent_sessions)]
        semaphore = asyncio.Semaphore(len(active_sessions))
        
        tasks = []
        for i, session_data in enumerate(active_sessions):
            task = asyncio.create_task(self._session_worker(session_data, i, semaphore))
            tasks.append(task)
            await asyncio.sleep(0.1)
        
        self._log(f"Запущено {len(tasks)} воркеров")
        
        monitor_task = asyncio.create_task(self._monitor_progress())
        await asyncio.gather(*tasks, return_exceptions=True)
        monitor_task.cancel()
        
        await self._print_final_stats()
    
    async def _monitor_progress(self, interval: float = 3.0):
        while True:
            try:
                await asyncio.sleep(interval)
                elapsed = time.time() - self.stats['start_time']
                rate = self.stats['total_sent'] / elapsed if elapsed > 0 else 0
                progress = (self.stats['total_sent'] / self.report_count * 100) if self.report_count > 0 else 0
                self._log(f"ПРОГРЕСС: {self.stats['total_sent']}/{self.report_count} ({progress:.1f}%) | Успех: {self.stats['successful']} | Ошибок: {self.stats['failed']} | Скорость: {rate:.1f}/сек")
            except asyncio.CancelledError:
                break
            except:
                pass
    
    async def _print_final_stats(self):
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['total_sent'] / elapsed if elapsed > 0 else 0
        
        self._log("=" * 60)
        self._log("КАМПАНИЯ ЗАВЕРШЕНА")
        self._log("=" * 60)
        self._log(f"Цель: {self.target}")
        self._log(f"Время: {elapsed:.1f} сек")
        self._log(f"Отправлено: {self.stats['total_sent']}")
        self._log(f"Успешно: {self.stats['successful']}")
        self._log(f"Ошибок: {self.stats['failed']}")
        self._log(f"Флуд: {self.stats['flood_limited']}")
        self._log(f"Скорость: {rate:.2f}/сек")
        self._log(f"Лог: {self.log_file}")
        self._log("=" * 60)
        
        stats_file = f"logs/stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'target': self.target,
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': elapsed,
                    'stats': self.stats,
                }, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def get_stats(self) -> Dict:
        return self.stats.copy()
    
    def is_campaign_finished(self) -> bool:
        return self.stats['total_sent'] >= self.report_count