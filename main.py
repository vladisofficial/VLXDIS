#!/usr/bin/env python3
# main.py
# VLXDIS Account Snoser v1.6.0 - Главный исполняемый файл
# Запуск: python main.py

import os
import sys
import json
import asyncio
import time
import random
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from colorama import init, Fore, Back, Style

# Инициализация colorama для Windows
init(autoreset=True)

# Импорт модулей
from config_manager import ConfigManager
from history_manager import HistoryManager
from session_manager import SessionManager
from report_engine import ReportEngine
from proxy_manager import ProxyManager

# ========== КОНСТАНТЫ ==========
VERSION = "1.6.0"
BUILD_DATE = "26.05.2026"
TELEGRAM_CONTACT = "@Itz_Vladis"
CONFIG_FILE = "config.json"

# Цветовая палитра: бирюзовый + белый
C_FRAME = Fore.CYAN
C_TEXT = Fore.WHITE
C_ACCENT = Fore.LIGHTCYAN_EX
C_BRIGHT = Fore.LIGHTWHITE_EX
C_SUCCESS = Fore.CYAN
C_ERROR = Fore.LIGHTRED_EX
C_WARNING = Fore.LIGHTYELLOW_EX
C_INFO = Fore.LIGHTCYAN_EX
C_PROMPT = Fore.CYAN
C_NUMBER = Fore.WHITE
C_TARGET = Fore.LIGHTWHITE_EX
C_DEV = Fore.LIGHTMAGENTA_EX

ASCII_LOGO = f"""
{C_FRAME}╔═════════════════════════════════════════════════════════╗
{C_FRAME}║                                                         ║
{C_FRAME}║      {C_TEXT}██╗   ██╗{C_FRAME}██╦      {C_TEXT}██╗  ██╗{C_FRAME}██████╗ {C_TEXT}██╗{C_FRAME}███████╗      {C_FRAME}║
{C_FRAME}║      {C_TEXT}██║   ██║{C_FRAME}██║      {C_TEXT}╚██╗██╔╝{C_FRAME}██╔══██╗{C_TEXT}██║{C_FRAME}██╔════╝      {C_FRAME}║
{C_FRAME}║      {C_TEXT}██║   ██║{C_FRAME}██║      {C_TEXT} ╚███╔╝ {C_FRAME}██║  ██║{C_TEXT}██║{C_FRAME}███████║      {C_FRAME}║
{C_FRAME}║      {C_TEXT}╚██╗ ██╔╝{C_FRAME}██║      {C_TEXT} ██╔██╗ {C_FRAME}██║  ██║{C_TEXT}██║{C_FRAME}╚════██║      {C_FRAME}║
{C_FRAME}║      {C_TEXT} ╚████╔╝ {C_FRAME}███████╗ {C_TEXT}██╔╝ ██╗{C_FRAME}██████╔╝{C_TEXT}██║{C_FRAME}███████║      {C_FRAME}║
{C_FRAME}║      {C_TEXT}  ╚═══╝  {C_FRAME}╚══════╝ {C_TEXT}╚═╝  ╚═╝{C_FRAME}╚═════╝ {C_TEXT}╚═╝{C_FRAME}╚══════╝      {C_FRAME}║
{C_FRAME}║                                                         ║
{C_FRAME}║         {C_TEXT}VLXDIS{C_FRAME}                                          ║
{C_FRAME}║         {C_ACCENT}Telegram Account Snoser v{VERSION}{C_FRAME}                  ║
{C_FRAME}║         {C_TEXT}Build: {BUILD_DATE}{C_FRAME} | {C_ACCENT}MTProto Layer 181{C_FRAME}           ║
{C_FRAME}║         {C_TEXT}Telegram: {C_BRIGHT}{TELEGRAM_CONTACT}{C_FRAME}                           ║
"""

# ========== КЛАСС ИНТЕРАКТИВНОГО МЕНЮ ==========
class InteractiveMenu:
    """
    VLXDIS - Интерактивное меню снос-системы.
    Telegram: @Itz_Vladis
    
    Возможности:
    - Ввод цели (username/ID)
    - Настройка параметров атаки
    - Управление прокси
    - Просмотр истории сносов
    - Сохранение/загрузка конфигураций
    - Выход в меню из любого места (0, menu, назад)
    - Выбор нескольких типов жалоб
    - Режим разработчика с дополнительными функциями
    """
    
    def __init__(self):
        self.config_manager = ConfigManager(CONFIG_FILE)
        self.history_manager = HistoryManager()
        self.session_manager = SessionManager()
        self.proxy_manager = ProxyManager()
        self.current_config = self.config_manager.load_config()
        self.report_engine = None
        
        # Режим разработчика
        self.dev_mode = self.current_config.get("dev_mode", False)
        
        # Путь к файлу main.py для горячей перезагрузки
        self.main_file = os.path.abspath(__file__) if os.path.exists(__file__) else os.path.join(os.getcwd(), "main.py")

    def clear_screen(self):
        """Очистка экрана консоли."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Вывод заголовка VLXDIS."""
        self.clear_screen()
        print(ASCII_LOGO, end='')
        
        proxy_count = len(self.proxy_manager.proxies)
        session_count = len(self.session_manager.get_cached_sessions())
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Левая часть всегда 12 символов
        if self.dev_mode:
            left1 = "VLXDIS [DEV]"
        else:
            left1 = "VLXDIS      "
        
        left2 = f"Proxy: {proxy_count}   "
        left2 = left2.ljust(12)[:12]
        
        line1 = f"{left1}| {date_str}"
        line2 = f"{left2}| Sessions: {session_count}"
        line3 = f"Contact: {TELEGRAM_CONTACT}"
        
        s1 = (57 - len(line1)) // 2
        s2 = (57 - len(line2)) // 2
        s3 = (57 - len(line3)) // 2
        e1 = 57 - len(line1) - s1
        e2 = 57 - len(line2) - s2
        e3 = 57 - len(line3) - s3
        
        color1 = C_DEV if self.dev_mode else C_SUCCESS
        
        print(f"{C_FRAME}╠═════════════════════════════════════════════════════════╣")
        print(f"{C_FRAME}║{color1}{' ' * s1}{line1}{' ' * e1}{C_FRAME}║")
        print(f"{C_FRAME}║{C_SUCCESS}{' ' * s2}{line2}{' ' * e2}{C_FRAME}║")
        print(f"{C_FRAME}║{C_SUCCESS}{' ' * s3}{line3}{' ' * e3}{C_FRAME}║")
        print(f"{C_FRAME}╚═════════════════════════════════════════════════════════╝")
    
    def get_user_input(self, prompt: str, default: str = "", input_type: str = "str") -> Any:
        """
        Получение пользовательского ввода с валидацией.
        Введите 'menu', '0', 'назад', 'exit' или 'cancel' для возврата в главное меню.
        
        Параметры:
            prompt: текст приглашения
            default: значение по умолчанию
            input_type: тип ввода (str, int, float, choice)
        """
        prompt_color = C_DEV if self.dev_mode else C_PROMPT
        default_str = f" [{default}]" if default else ""
        full_prompt = f"{prompt_color}[VLXDIS] {prompt}{default_str} {C_WARNING}(menu - назад){prompt_color}: {C_TEXT}"
        
        while True:
            try:
                user_input = input(full_prompt).strip()
                
                # Проверка на выход в меню
                if user_input.lower() in ['0', 'menu', 'назад', 'exit', 'cancel']:
                    print(f"{C_WARNING}[VLXDIS] Возврат в главное меню...")
                    time.sleep(0.5)
                    return None
                
                if not user_input and default:
                    return default
                
                if input_type == "int":
                    return int(user_input)
                elif input_type == "float":
                    return float(user_input)
                elif input_type == "choice":
                    return user_input.lower()
                else:
                    return user_input
                    
            except ValueError:
                print(f"{C_ERROR}[VLXDIS] Ошибка: неверный формат ввода. Ожидается {input_type}")
                print(f"{C_WARNING}[VLXDIS] Введите 'menu' для возврата в главное меню")
            except KeyboardInterrupt:
                print(f"\n{C_WARNING}[VLXDIS] Возврат в главное меню...")
                time.sleep(0.5)
                return None
    
    def print_menu_option(self, number: int, text: str, color: str = C_TEXT):
        """Вывод пункта меню VLXDIS."""
        if isinstance(number, str):
            print(f"  {C_NUMBER}[{number}] {color}{text}")
        else:
            print(f"  {C_NUMBER}[{number}] {color}{text}")
    
    def print_section_title(self, text: str):
        """Вывод заголовка секции."""
        print(f"{C_TEXT}  {text}")
        print()
    
    def print_info(self, text: str):
        """Вывод информационного текста."""
        print(f"  {C_ACCENT}{text}")
    
    def show_main_menu(self) -> str:
        """Главное меню VLXDIS."""
        self.print_header()
        
        print(f"{C_TEXT}  VLXDIS ГЛАВНОЕ МЕНЮ:")
        print()
        self.print_menu_option(1, "[+] Начать новый снос", C_ACCENT)
        self.print_menu_option(2, "[*] Настройки конфигурации", C_SUCCESS)
        self.print_menu_option(3, "[i] Просмотр истории сносов", C_ACCENT)
        self.print_menu_option(4, "[@] Управление прокси", C_BRIGHT)
        self.print_menu_option(5, "[#] Управление сессиями", C_ACCENT)
        self.print_menu_option(6, "[$] Сохранить конфигурацию", C_SUCCESS)
        self.print_menu_option(7, "[=] Статистика VLXDIS", C_ACCENT)
        self.print_menu_option(8, "[?] Инфо / Руководство", C_BRIGHT)
        self.print_menu_option(9, "[@] OSINT поиск цели", C_ACCENT)
        
        if self.dev_mode:
            self.print_menu_option(10, "[!] Режим разработчика: ВКЛ", C_DEV)
            self.print_menu_option("D1", "    [~] Обновить меню", C_DEV)
        else:
            self.print_menu_option(10, "[!] Режим разработчика: ВЫКЛ", C_SUCCESS)
        
        self.print_menu_option(0, "[x] Выход", C_ERROR)
        print()
        
        choice = self.get_user_input("Выберите пункт меню", "1", "str")
        
        if choice is None:
            return "exit"
        
        # Обработка выбора
        try:
            choice_int = int(choice)
        except ValueError:
            choice_int = -1
        
        # Пункты разработчика (буквенные)
        if choice.upper() == "D1" and self.dev_mode:
            return self.menu_dev_reload()
        
        menu_actions = {
            1: self.menu_new_snos,
            2: self.menu_settings,
            3: self.menu_history,
            4: self.menu_proxy,
            5: self.menu_sessions,
            6: self.menu_save_config,
            7: self.menu_statistics,
            8: self.menu_info,
            9: self.menu_osint,
            10: self.menu_toggle_dev_mode,
            0: self.menu_exit
        }
        
        action = menu_actions.get(choice_int, self.show_main_menu)
        return action()
    
    def menu_toggle_dev_mode(self) -> str:
        """Переключение режима разработчика."""
        self.dev_mode = not self.dev_mode
        self.current_config["dev_mode"] = self.dev_mode
        self.config_manager.save_config(self.current_config)
        
        if self.dev_mode:
            print(f"{C_DEV}[VLXDIS] Режим разработчика ВКЛЮЧЕН")
            print(f"{C_DEV}[VLXDIS] Доступны дополнительные пункты меню")
        else:
            print(f"{C_TEXT}[VLXDIS] Режим разработчика ВЫКЛЮЧЕН")
        
        time.sleep(1)
        return "main_menu"

    def print_separator(self):
        """Вывод разделителя."""
        print(f"{C_FRAME}╠══════════════════════════════════════════════════════════╣")
    
    def menu_dev_reload(self) -> str:
        """Функция разработчика: перезагрузка main.py без выхода из программы."""
        self.print_header()
        print(f"{C_DEV}  VLXDIS | ОБНОВЛЕНИЕ МЕНЮ")
        self.print_separator()
        print()
        print(f"  {C_TEXT}Выполняется перезагрузка main.py...")
        print(f"  {C_ACCENT}Файл: {self.main_file}")
        print()
        
        confirm = self.get_user_input("Перезагрузить меню с новым кодом? (y/n)", "y", "choice")
        
        if confirm == 'y':
            print(f"{C_WARNING}[VLXDIS] Сохранение текущего состояния...")
            
            # Сохраняем конфигурацию
            self.config_manager.save_config(self.current_config)
            
            print(f"{C_SUCCESS}[VLXDIS] Состояние сохранено")
            print(f"{C_DEV}[VLXDIS] Запуск обновленной версии...")
            print(f"{C_DEV}[VLXDIS] Текущий процесс будет заменен новым")
            print()
            print(f"{C_WARNING}  Окно перезапустится автоматически через 2 секунды...")
            time.sleep(2)
            
            # Запускаем новый процесс и выходим из текущего
            try:
                python_exe = sys.executable
                script_path = self.main_file
                
                # Запускаем новый процесс
                if os.name == 'nt':
                    subprocess.Popen([python_exe, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([python_exe, script_path])
                
                # Выходим из текущего
                sys.exit(0)
            except Exception as e:
                print(f"{C_ERROR}[VLXDIS] Ошибка перезагрузки: {e}")
                print(f"{C_WARNING}[VLXDIS] Попробуйте перезапустить вручную: python main.py")
                self.get_user_input("Нажмите Enter для возврата", "", "str")
                return "main_menu"
        else:
            print(f"{C_WARNING}[VLXDIS] Перезагрузка отменена")
            time.sleep(1)
            return "main_menu"
    
    def menu_new_snos(self) -> str:
        """Меню нового сноса VLXDIS."""
        self.print_header()
        print(f"{C_BRIGHT}  VLXDIS | НАЧАЛО НОВОГО СНОСА")
        print(f"{C_WARNING}  Введите 'menu' в любой момент для возврата")
        self.print_separator()
        print()
        
        # Ввод цели
        self.print_section_title("Введите цель для сноса:")
        self.print_info("Форматы: @username, +79XXXXXXXXX")
        print()
        target = self.get_user_input("Цель (@username или +79XXXXXXXXX)", "", "str")
        
        if target is None:
            return "main_menu"
        if not target:
            print(f"{C_ERROR}[VLXDIS] Цель не указана. Возврат в меню.")
            time.sleep(2)
            return "main_menu"
        
        target = target.replace('@', '').replace('+', '').replace(' ', '')
        
        print()
        
        # Выбор типа жалоб
        self.print_section_title("Типы жалоб для отправки:")
        self.print_info("1. SPAM (Спам)")
        self.print_info("2. VIOLENCE (Насилие)")
        self.print_info("3. PORNOGRAPHY (Порнография)")
        self.print_info("4. CHILD_ABUSE (Насилие над детьми)")
        self.print_info("5. COPYRIGHT (Нарушение авторских прав)")
        self.print_info("6. OTHER (Другое)")
        self.print_info("7. ALL (Все типы) [Рекомендуется]")
        self.print_info("8. ВЫБРАТЬ НЕСКОЛЬКО (указать номера через запятую)")
        print()
        
        report_choice = self.get_user_input("Выберите типы жалоб (1-8)", "7", "str")
        
        if report_choice is None:
            return "main_menu"
        
        report_type_map = {
            "1": ["inputReportReasonSpam"],
            "2": ["inputReportReasonViolence"],
            "3": ["inputReportReasonPornography"],
            "4": ["inputReportReasonChildAbuse"],
            "5": ["inputReportReasonCopyright"],
            "6": ["inputReportReasonOther"],
            "7": ["inputReportReasonSpam", "inputReportReasonViolence", 
                "inputReportReasonPornography", "inputReportReasonChildAbuse",
                "inputReportReasonCopyright", "inputReportReasonOther"]
        }
        
        type_labels = {
            "1": "SPAM", "2": "VIOLENCE", "3": "PORNOGRAPHY",
            "4": "CHILD_ABUSE", "5": "COPYRIGHT", "6": "OTHER"
        }
        
        if report_choice == "8":
            print(f"\n  {C_TEXT}Введите номера типов через запятую:")
            self.print_info("Пример: 1,3,5 (SPAM + PORNOGRAPHY + COPYRIGHT)")
            self.print_info("Пример: 1,6 (SPAM + OTHER)")
            print()
            
            multi_choice = self.get_user_input("Номера типов через запятую", "1,6", "str")
            
            if multi_choice is None:
                return "main_menu"
            
            selected_types = []
            type_names = []
            
            for num in multi_choice.split(","):
                num = num.strip()
                if num in report_type_map and num != "7":
                    selected_types.extend(report_type_map[num])
                    if num in type_labels:
                        type_names.append(type_labels[num])
            
            if not selected_types:
                print(f"{C_ERROR}[VLXDIS] Не выбрано ни одного типа. Использую ALL.")
                selected_types = report_type_map["7"]
                type_names = ["ALL"]
            
            print(f"{C_SUCCESS}[VLXDIS] Выбраны типы: {', '.join(type_names)}")
            
        else:
            selected_types = report_type_map.get(report_choice, report_type_map["7"])
        
        print()
        
        # Количество жалоб
        self.print_section_title("Количество жалоб для отправки:")
        self.print_info("Минимум: 150 | Рекомендуется: 500 | Максимум: 5000")
        print(f"  {C_WARNING}Больше жалоб = быстрее снос, но больше расход аккаунтов")
        print()
        
        report_count = self.get_user_input("Количество жалоб", "500", "int")
        
        if report_count is None:
            return "main_menu"
        
        print()
        
        # Количество параллельных сессий
        self.print_section_title("Количество параллельных сессий:")
        self.print_info("Рекомендуется: 50 | Максимум: 200")
        print()
        
        concurrent = self.get_user_input("Параллельных сессий", "50", "int")
        
        if concurrent is None:
            return "main_menu"
        
        print()
        
        # Сообщение жалобы
        self.print_section_title("Текст жалобы (на английском):")
        self.print_info("По умолчанию: стандартное сообщение о мошенничестве")
        print()
        
        default_message = "This account is involved in fraudulent activities, phishing scams, and spreading malware. Immediate action required."
        custom_message = self.get_user_input("Текст жалобы (Enter для стандартного)", default_message, "str")
        
        if custom_message is None:
            return "main_menu"
        
        print()
        
        # Задержки
        self.print_section_title("Задержки между жалобами (секунды):")
        self.print_info("Рекомендуется: 0.5 - 2.0 (рандомизировано)")
        print()
        
        delay_min = self.get_user_input("Минимальная задержка (сек)", "0.5", "float")
        
        if delay_min is None:
            return "main_menu"
        
        delay_max = self.get_user_input("Максимальная задержка (сек)", "2.0", "float")
        
        if delay_max is None:
            return "main_menu"
        
        print()
        
        # Подтверждение
        self.print_separator()
        print(f"{C_TEXT}  VLXDIS | ПОДТВЕРЖДЕНИЕ СНОСА:")
        print(f"{C_BRIGHT}  Цель: {target}")
        print(f"{C_BRIGHT}  Типы жалоб: {', '.join(selected_types)}")
        print(f"{C_BRIGHT}  Количество: {report_count}")
        print(f"{C_BRIGHT}  Параллельных сессий: {concurrent}")
        print(f"{C_BRIGHT}  Задержка: {delay_min}-{delay_max} сек")
        self.print_separator()
        print()
        
        confirm = self.get_user_input(f"Начать снос? (y/n)", "y", "choice")
        
        if confirm is None:
            return "main_menu"
        
        if confirm == 'y':
            snos_config = {
                "target": target,
                "report_types": selected_types,
                "report_count": report_count,
                "concurrent_sessions": concurrent,
                "report_message": custom_message,
                "delay_range": (delay_min, delay_max),
                "timestamp": datetime.now().isoformat(),
                "session_pool": self.session_manager.get_cached_sessions(),
                "proxy_list": self.proxy_manager.proxies,
                "software": "VLXDIS",
                "version": VERSION,
                "telegram_contact": TELEGRAM_CONTACT
            }
            
            record_id = self.history_manager.add_snos_record(snos_config)
            snos_config['record_id'] = record_id
            asyncio.run(self._execute_snos_async(snos_config))
            return "main_menu"
        else:
            print(f"{C_WARNING}[VLXDIS] Снос отменен")
            time.sleep(1)
            return "main_menu"
    
    async def _execute_snos_async(self, config: Dict):
        """Асинхронное выполнение сноса VLXDIS."""
        self.print_header()
        print(f"{C_BRIGHT}  VLXDIS | СНОС ЗАПУЩЕН")
        self.print_separator()
        print(f"  {C_ACCENT}  Telegram: {TELEGRAM_CONTACT}")
        self.print_separator()
        
        # Получаем ID записи из конфига
        record_id = config.get('record_id')
        
        self.report_engine = ReportEngine(config)
        await self.report_engine.run_report_campaign()
        
        # Обновляем статус в истории
        if record_id:
            stats = self.report_engine.get_stats()
            elapsed = time.time() - stats['start_time']
            self.history_manager.mark_completed(record_id, {
                'reports_sent': stats['total_sent'],
                'successful': stats['successful'],
                'failed': stats['failed'],
                'duration_seconds': elapsed
            })
        
        print(f"\n{C_SUCCESS}  VLXDIS | Снос завершен!")
        print(f"{C_ACCENT}  Контакт: {TELEGRAM_CONTACT}")
        self.print_separator()
        self.get_user_input("Нажмите Enter для возврата в меню", "", "str")
    
    def menu_settings(self) -> str:
        """Меню настроек VLXDIS."""
        self.print_header()
        print(f"{C_ACCENT}  VLXDIS | НАСТРОЙКИ КОНФИГУРАЦИИ")
        self.print_separator()
        print()
        
        current = self.current_config
        
        print(f"{C_TEXT}  Текущие настройки:")
        print(f"  {C_ACCENT}1. API ID: {C_TEXT}{current.get('api_id', 2040)}")
        print(f"  {C_ACCENT}2. API Hash: {C_TEXT}{current.get('api_hash', 'b18441a1ff607e10a989891a5462e627')}")
        print(f"  {C_ACCENT}3. Максимальное время сноса (мин): {C_TEXT}{current.get('max_snos_time', 120)}")
        print(f"  {C_ACCENT}4. Автосохранение истории: {C_TEXT}{current.get('auto_save', True)}")
        print(f"  {C_ACCENT}5. Логирование: {C_TEXT}{current.get('logging', True)}")
        print(f"  {C_ACCENT}6. Контакт Telegram: {C_TEXT}{current.get('telegram_contact', TELEGRAM_CONTACT)}")
        print(f"  {C_ACCENT}7. Режим разработчика: {C_DEV if current.get('dev_mode', False) else C_TEXT}{current.get('dev_mode', False)}")
        print(f"  {C_WARNING}0. Назад")
        print()
        
        choice = self.get_user_input("Выберите параметр для изменения", "0", "int")
        
        if choice is None or choice == 0:
            return "main_menu"
        
        if choice == 1:
            new_val = self.get_user_input("Новый API ID", str(current.get('api_id', 2040)), "int")
            if new_val is not None:
                self.current_config['api_id'] = new_val
        elif choice == 2:
            new_val = self.get_user_input("Новый API Hash", current.get('api_hash', 'b18441a1ff607e10a989891a5462e627'), "str")
            if new_val is not None:
                self.current_config['api_hash'] = new_val
        elif choice == 3:
            new_val = self.get_user_input("Максимальное время (мин)", str(current.get('max_snos_time', 120)), "int")
            if new_val is not None:
                self.current_config['max_snos_time'] = new_val
        elif choice == 4:
            new_val = self.get_user_input("Автосохранение (True/False)", str(current.get('auto_save', True)), "choice")
            if new_val is not None:
                self.current_config['auto_save'] = new_val.lower() == 'true'
        elif choice == 5:
            new_val = self.get_user_input("Логирование (True/False)", str(current.get('logging', True)), "choice")
            if new_val is not None:
                self.current_config['logging'] = new_val.lower() == 'true'
        elif choice == 6:
            new_val = self.get_user_input("Контакт Telegram", current.get('telegram_contact', TELEGRAM_CONTACT), "str")
            if new_val is not None:
                self.current_config['telegram_contact'] = new_val
        elif choice == 7:
            self.dev_mode = not self.dev_mode
            self.current_config['dev_mode'] = self.dev_mode
            if self.dev_mode:
                print(f"{C_DEV}[VLXDIS] Режим разработчика ВКЛЮЧЕН")
            else:
                print(f"{C_TEXT}[VLXDIS] Режим разработчика ВЫКЛЮЧЕН")
        
        self.config_manager.save_config(self.current_config)
        print(f"{C_SUCCESS}[VLXDIS] Настройки сохранены!")
        time.sleep(1)
        return "main_menu"
    
    def menu_history(self) -> str:
        """Меню просмотра истории VLXDIS."""
        self.print_header()
        print(f"{C_SUCCESS}  VLXDIS | ИСТОРИЯ СНОСОВ")
        self.print_separator()
        print()
        
        history = self.history_manager.get_all_records()
        
        if not history:
            print(f"{C_WARNING}  История пуста. Выполните первый снос.")
            print()
            self.get_user_input("Нажмите Enter для возврата", "", "str")
            return "main_menu"
        
        print(f"{C_TEXT}  Последние сносы VLXDIS:")
        print(f"  {C_ACCENT}{'Дата':<20} {'Цель':<25} {'Жалоб':<8} {'Статус':<15}")
        print(f"  {C_TEXT}{'-'*68}")
        
        for record in history[-10:]:
            date_str = record.get('timestamp', 'N/A')[:19].replace('T', ' ')
            target = record.get('target', 'N/A')[:24]
            count = record.get('report_count', 'N/A')
            status = record.get('status', 'UNKNOWN')
            
            color = C_SUCCESS if status == 'COMPLETED' else C_ERROR if status == 'FAILED' else C_WARNING
            print(f"  {C_TEXT}{date_str:<20} {C_ACCENT}{target:<25} {C_TEXT}{str(count):<8} {color}{status:<15}")
        
        print()
        print(f"{C_TEXT}  Всего записей: {len(history)}")
        print()
        self.print_menu_option(1, "[>] Просмотреть детальный отчет", C_ACCENT)
        self.print_menu_option(2, "[$] Экспорт истории в JSON", C_SUCCESS)
        self.print_menu_option(3, "[!] Очистить историю", C_ERROR)
        self.print_menu_option(0, "[<] Назад", C_TEXT)
        print()
        
        choice = self.get_user_input("Выберите действие", "0", "int")
        
        if choice is None or choice == 0:
            return "main_menu"
        
        if choice == 1:
            record_id = self.get_user_input("Введите номер записи (1-последняя)", "1", "int")
            if record_id is not None and record_id <= len(history):
                record = history[-record_id]
                self._show_detailed_report(record)
        elif choice == 2:
            exported_path = self.history_manager.export_history()
            print(f"{C_SUCCESS}[VLXDIS] История экспортирована в {exported_path}")
            time.sleep(1)
        elif choice == 3:
            confirm = self.get_user_input("Удалить ВСЮ историю? (y/n)", "n", "choice")
            if confirm == 'y':
                self.history_manager.clear_history()
                print(f"{C_SUCCESS}[VLXDIS] История очищена!")
                time.sleep(1)
        
        return "main_menu"
    
    def _show_detailed_report(self, record: Dict):
        """Показ детального отчета VLXDIS."""
        self.print_header()
        print(f"{C_SUCCESS}  VLXDIS | ДЕТАЛЬНЫЙ ОТЧЕТ")
        self.print_separator()
        print()
        
        try:
            target = record.get('target', 'N/A') if record else 'N/A'
            timestamp = record.get('timestamp', 'N/A') if record else 'N/A'
            completion = record.get('completion_time', 'В процессе') if record else 'N/A'
            status = record.get('status', 'UNKNOWN') if record else 'UNKNOWN'
            report_count = record.get('report_count', 0) if record else 0
            reports_sent = record.get('reports_sent', 0) if record else 0
            successful = record.get('successful', 0) if record else 0
            failed = record.get('failed', 0) if record else 0
            report_types = record.get('report_types', []) if record else []
            concurrent = record.get('concurrent_sessions', 0) if record else 0
            proxy_list = record.get('proxy_list', []) if record else []
            duration = record.get('duration_seconds', 0) if record else 0
            software = record.get('software', 'VLXDIS') if record else 'VLXDIS'
            version = record.get('version', VERSION) if record else VERSION
            contact = record.get('telegram_contact', TELEGRAM_CONTACT) if record else TELEGRAM_CONTACT
        except Exception as e:
            print(f"{C_ERROR}Ошибка чтения записи: {e}")
            self.get_user_input("Нажмите Enter для возврата", "", "str")
            return
        
        print(f"  {C_TEXT}Цель: {C_BRIGHT}{target}")
        print(f"  {C_TEXT}Дата начала: {C_ACCENT}{timestamp}")
        print(f"  {C_TEXT}Дата завершения: {C_ACCENT}{completion}")
        print(f"  {C_TEXT}Статус: {status}")
        print(f"  {C_TEXT}Количество жалоб: {C_ACCENT}{report_count}")
        print(f"  {C_TEXT}Отправлено: {C_ACCENT}{reports_sent}")
        print(f"  {C_TEXT}Успешно: {C_SUCCESS}{successful}")
        print(f"  {C_TEXT}Ошибок: {C_ERROR}{failed}")
        print(f"  {C_TEXT}Типы жалоб: {C_ACCENT}{', '.join(report_types)}")
        print(f"  {C_TEXT}Параллельных сессий: {C_ACCENT}{concurrent}")
        print(f"  {C_TEXT}Использовано прокси: {C_ACCENT}{len(proxy_list)}")
        print(f"  {C_TEXT}Длительность: {C_ACCENT}{duration:.1f} сек")
        print(f"  {C_TEXT}ПО: {C_ACCENT}{software} v{version}")
        print(f"  {C_TEXT}Контакт: {C_ACCENT}{contact}")
        print()
        
        self.get_user_input("Нажмите Enter для возврата", "", "str")
    
    def menu_proxy(self) -> str:
        """Меню управления прокси VLXDIS."""
        self.print_header()
        print(f"{C_ACCENT}  VLXDIS | УПРАВЛЕНИЕ ПРОКСИ")
        self.print_separator()
        print()
        
        proxies = self.proxy_manager.proxies
        print(f"  {C_TEXT}Загружено прокси: {C_SUCCESS}{len(proxies)}")
        print()
        
        self.print_menu_option(1, "[+] Загрузить прокси из файла", C_ACCENT)
        self.print_menu_option(2, "[+] Добавить прокси вручную", C_SUCCESS)
        self.print_menu_option(3, "[~] Проверить все прокси", C_WARNING)
        self.print_menu_option(4, "[i] Показать список прокси", C_TEXT)
        self.print_menu_option(5, "[!] Очистить список прокси", C_ERROR)
        self.print_menu_option(0, "[<] Назад", C_TEXT)
        print()
        
        choice = self.get_user_input("Выберите действие", "0", "int")
        
        if choice is None or choice == 0:
            return "main_menu"
        
        if choice == 1:
            filepath = self.get_user_input("Путь к файлу прокси", "socks5_proxies.txt", "str")
            if filepath is not None:
                loaded = self.proxy_manager.load_from_file(filepath)
                print(f"{C_SUCCESS}[VLXDIS] Загружено {loaded} прокси")
                time.sleep(1)
        elif choice == 2:
            proxy_str = self.get_user_input("Прокси (ip:port или ip:port:user:pass)", "", "str")
            if proxy_str is not None and self.proxy_manager.add_proxy(proxy_str):
                print(f"{C_SUCCESS}[VLXDIS] Прокси добавлен")
                time.sleep(1)
        elif choice == 3:
            print(f"{C_WARNING}[VLXDIS] Проверка прокси...")
            valid = asyncio.run(self.proxy_manager.check_all_proxies())
            print(f"{C_SUCCESS}[VLXDIS] Рабочих прокси: {valid}")
            time.sleep(2)
        elif choice == 4:
            self.print_header()
            print(f"{C_TEXT}  VLXDIS | Список прокси:")
            for i, proxy in enumerate(proxies[:20], 1):
                print(f"  {C_ACCENT}{i}. {C_TEXT}{proxy.get('hostname')}:{proxy.get('port')}")
            print()
            self.get_user_input("Нажмите Enter для возврата", "", "str")
        elif choice == 5:
            confirm = self.get_user_input("Очистить список? (y/n)", "n", "choice")
            if confirm == 'y':
                self.proxy_manager.clear_proxies()
                print(f"{C_SUCCESS}[VLXDIS] Список очищен")
                time.sleep(1)
        
        return "main_menu"
    
    def menu_sessions(self) -> str:
        """Меню управления сессиями VLXDIS."""
        self.print_header()
        print(f"{C_ACCENT}  VLXDIS | УПРАВЛЕНИЕ СЕССИЯМИ")
        self.print_separator()
        print()
        
        sessions = self.session_manager.get_cached_sessions()
        print(f"  {C_TEXT}Активных сессий: {C_SUCCESS}{len(sessions)}")
        print()
        
        self.print_menu_option(1, "[+] Загрузить сессии из файла", C_ACCENT)
        self.print_menu_option(2, "[+] Создать новую сессию", C_SUCCESS)
        self.print_menu_option(3, "[~] Проверить валидность сессий", C_WARNING)
        self.print_menu_option(4, "[i] Показать список сессий", C_TEXT)
        self.print_menu_option(5, "[$] Экспорт сессий в файл", C_ACCENT)
        self.print_menu_option(0, "[<] Назад", C_TEXT)
        print()
        
        choice = self.get_user_input("Выберите действие", "0", "int")
        
        if choice is None or choice == 0:
            return "main_menu"
        
        if choice == 1:
            filepath = self.get_user_input("Путь к файлу сессий", "session_strings.txt", "str")
            if filepath is not None:
                loaded = self.session_manager.load_from_file(filepath)
                print(f"{C_SUCCESS}[VLXDIS] Загружено {loaded} сессий")
                time.sleep(1)
        elif choice == 2:
            phone = self.get_user_input("Номер телефона (+79XXXXXXXXX)", "", "str")
            if phone is not None and phone:
                print(f"{C_WARNING}[VLXDIS] Создание сессии для {phone}")
                session = asyncio.run(self.session_manager.create_session(phone))
                if session:
                    print(f"{C_SUCCESS}[VLXDIS] Сессия создана!")
                    time.sleep(1)
        elif choice == 3:
            print(f"{C_WARNING}[VLXDIS] Проверка сессий...")
            valid = asyncio.run(self.session_manager.validate_all_sessions())
            print(f"{C_SUCCESS}[VLXDIS] Валидных сессий: {valid}")
            time.sleep(2)
        elif choice == 4:
            self.print_header()
            print(f"{C_TEXT}  VLXDIS | Список сессий:")
            for i, sess in enumerate(sessions[:20], 1):
                print(f"  {C_ACCENT}{i}. {C_TEXT}{sess.get('phone', 'Unknown')} | Отчетов: {sess.get('reports_sent', 0)}")
            print()
            self.get_user_input("Нажмите Enter для возврата", "", "str")
        elif choice == 5:
            filepath = self.get_user_input("Путь для экспорта", "exported_sessions.txt", "str")
            if filepath is not None:
                self.session_manager.export_to_file(filepath)
                print(f"{C_SUCCESS}[VLXDIS] Сессии экспортированы в {filepath}")
                time.sleep(1)
        
        return "main_menu"
    
    def menu_save_config(self) -> str:
        """Сохранение конфигурации VLXDIS."""
        self.print_header()
        print(f"{C_WARNING}  VLXDIS | СОХРАНЕНИЕ КОНФИГУРАЦИИ")
        self.print_separator()
        print()
        
        filename = self.get_user_input("Имя файла конфигурации", f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "str")
        
        if filename is None:
            return "main_menu"
        
        config_to_save = {
            **self.current_config,
            "proxy_count": len(self.proxy_manager.proxies),
            "session_count": len(self.session_manager.get_cached_sessions()),
            "saved_at": datetime.now().isoformat(),
            "software": "VLXDIS",
            "version": VERSION,
            "build_date": BUILD_DATE,
            "telegram_contact": TELEGRAM_CONTACT
        }
        
        self.config_manager.save_config(config_to_save, f"configs/{filename}.json")
        print(f"{C_SUCCESS}[VLXDIS] Конфигурация сохранена в configs/{filename}.json")
        time.sleep(1)
        return "main_menu"
    
    def menu_statistics(self) -> str:
        """Показ статистики VLXDIS."""
        self.print_header()
        print(f"{C_TEXT}  VLXDIS | СТАТИСТИКА СИСТЕМЫ")
        self.print_separator()
        print()
        
        history = self.history_manager.get_all_records()
        total_reports = sum(r.get('reports_sent', 0) for r in history)
        total_successful = sum(r.get('successful', 0) for r in history)
        completed_snoses = sum(1 for r in history if r.get('status') == 'COMPLETED')
        
        print(f"  {C_TEXT}Всего сносов: {C_SUCCESS}{len(history)}")
        print(f"  {C_TEXT}Завершенных: {C_SUCCESS}{completed_snoses}")
        print(f"  {C_TEXT}Всего жалоб: {C_BRIGHT}{total_reports}")
        print(f"  {C_TEXT}Успешных жалоб: {C_SUCCESS}{total_successful}")
        if total_reports > 0:
            print(f"  {C_TEXT}Процент успеха: {C_SUCCESS}{(total_successful/total_reports*100):.1f}%")
        else:
            print(f"  {C_TEXT}Процент успеха: {C_SUCCESS}0.0%")
        print(f"  {C_TEXT}Прокси в пуле: {C_ACCENT}{len(self.proxy_manager.proxies)}")
        print(f"  {C_TEXT}Сессий в кеше: {C_ACCENT}{len(self.session_manager.get_cached_sessions())}")
        print(f"  {C_TEXT}Версия: {C_ACCENT}VLXDIS v{VERSION}")
        print(f"  {C_TEXT}Build: {C_ACCENT}{BUILD_DATE}")
        print(f"  {C_TEXT}Контакт: {C_ACCENT}{TELEGRAM_CONTACT}")
        print(f"  {C_TEXT}Режим разработчика: {C_DEV if self.dev_mode else C_TEXT}{self.dev_mode}")
        print()
        
        self.get_user_input("Нажмите Enter для возврата", "", "str")
        return "main_menu"

    def menu_info(self) -> str:
        """Инфо и руководство."""
        self.print_header()
        print(f"{C_ACCENT}  VLXDIS | ИНФО / РУКОВОДСТВО")
        self.print_separator()
        print()
        print(f"{C_TEXT}  ДОБАВЛЕНИЕ СЕССИЙ:")
        print(f"  {C_ACCENT}1. Купить аккаунты Telegram (MarketGram, CrazyShops)")
        print(f"  {C_ACCENT}2. Получить строки сессий (session_string)")
        print(f"  {C_ACCENT}3. Вставить в файл session_strings.txt")
        print(f"  {C_ACCENT}4. Одна строка = одна сессия = одна строка файла")
        print()
        print(f"{C_TEXT}  ДОБАВЛЕНИЕ ПРОКСИ:")
        print(f"  {C_ACCENT}1. Купить SOCKS5 прокси (Proxy6.net, Asocks.io)")
        print(f"  {C_ACCENT}2. Формат: ip:port:user:pass или ip:port")
        print(f"  {C_ACCENT}3. Вставить в файл socks5_proxies.txt")
        print(f"  {C_ACCENT}4. Каждый прокси с новой строки")
        print()
        print(f"{C_TEXT}  НАСТРОЙКА API:")
        print(f"  {C_ACCENT}1. Зайти на my.telegram.org")
        print(f"  {C_ACCENT}2. Создать приложение (API Development Tools)")
        print(f"  {C_ACCENT}3. Скопировать api_id и api_hash в config.json")
        print()
        print(f"{C_TEXT}  ЗАПУСК СНОСА:")
        print(f"  {C_ACCENT}1. Выбрать пункт 1 в главном меню")
        print(f"  {C_ACCENT}2. Ввести цель: @username или +79123456789")
        print(f"  {C_ACCENT}3. Выбрать типы жалоб (рекомендуется ALL - пункт 7)")
        print(f"  {C_ACCENT}4. Указать количество жалоб (рекомендуется 30-40 на аккаунт)")
        print(f"  {C_ACCENT}5. Указать количество параллельных сессий")
        print(f"  {C_ACCENT}6. Ввести текст жалобы или Enter для стандартного")
        print(f"  {C_ACCENT}7. Указать задержки между жалобами (0.5-2.0 сек)")
        print()
        print(f"{C_TEXT}  СОВЕТЫ:")
        print(f"  {C_ACCENT}- Не ставь больше 50 жалоб на 1 аккаунт за раз")
        print(f"  {C_ACCENT}- Используй прокси из разных стран")
        print(f"  {C_ACCENT}- Для цели без @username используй номер телефона")
        print(f"  {C_ACCENT}- NFT-username не поддерживаются, нужен обычный")
        print(f"  {C_ACCENT}- Проверяй сессии перед сносом (пункт 5 -> 3)")
        print()
        print(f"{C_TEXT}  БОТ:")
        print(f"  {C_ACCENT}- Запуск: python bot.py")
        print(f"  {C_ACCENT}- Команды: /snos, /status, /stop, /stats")
        print(f"  {C_ACCENT}- Добавление сессий: /addsession")
        print(f"  {C_ACCENT}- Добавление прокси: /addproxy")
        print(f"  {C_ACCENT}- Управление админами: /addadmin, /adminlist")
        print()
        self.get_user_input("Нажмите Enter для возврата", "", "str")
        return "main_menu"
    
    def menu_osint(self) -> str:
        """OSINT поиск информации о цели."""
        self.print_header()
        print(f"{C_ACCENT}  VLXDIS | OSINT ПОИСК ЦЕЛИ")
        self.print_separator()
        print()
        print(f"{C_TEXT}  Выберите тип поиска:")
        print(f"  {C_ACCENT}[1] Поиск username по соцсетям (Sherlock)")
        print(f"  {C_ACCENT}[2] Поиск по номеру телефона (Telegram)")
        print(f"  {C_ACCENT}[3] Поиск по ID (Telegram)")
        print(f"  {C_ACCENT}[4] Поиск email в утечках")
        print(f"  {C_ACCENT}[5] Поиск в слитых базах (LeakCheck)")
        print(f"  {C_ACCENT}[0] Назад")
        print()
        
        choice = self.get_user_input("Выберите тип поиска", "0", "str")
        
        if choice is None or choice == '0':
            return "main_menu"
        
        from osint_engine import OSINTEngine
        
        # ========== 1. Sherlock username ==========
        if choice == '1':
            target = self.get_user_input("Username (без @)", "", "str")
            if target is None or not target:
                return "main_menu"
            
            target = target.strip().lstrip('@')
            self.print_separator()
            print()
            print(f"{C_TEXT}  Ищем {C_BRIGHT}{target}{C_TEXT} по 20+ соцсетям...")
            print()
            
            result = OSINTEngine.search_username(target)
            
            if result["found_sites"]:
                print(f"  {C_SUCCESS}Найдено: {len(result['found_sites'])} сайтов")
                for site in result["found_sites"]:
                    print(f"  {C_SUCCESS}[+] {C_ACCENT}{site}")
            else:
                print(f"  {C_WARNING}Ничего не найдено")
            
            if result["errors"]:
                for err in result["errors"]:
                    print(f"  {C_ERROR}{err}")
        
        # ========== 2. Поиск по номеру телефона ==========
        elif choice == '2':
            phone = self.get_user_input("Номер телефона (+79123456789)", "", "str")
            if phone is None or not phone:
                return "main_menu"
            
            self.print_separator()
            print()
            print(f"  {C_TEXT}Ищем {C_BRIGHT}{phone}{C_TEXT} через Telegram...")
            print()
            
            from session_manager import SessionManager
            sm = SessionManager()
            sessions = sm.get_cached_sessions()
            
            if not sessions:
                print(f"  {C_ERROR}Нет активных сессий. Добавьте сессии через меню.")
            else:
                from pyrogram import Client
                from proxy_manager import ProxyManager
                import random
                config = self.config_manager.load_config()
                
                pm = ProxyManager()
                proxy = random.choice(pm.proxies) if pm.proxies else None
                
                if proxy:
                    print(f"  {C_ACCENT}Использую прокси: {proxy.get('hostname')}:{proxy.get('port')}")
                
                async def search_phone():
                    client = Client(
                        name="osint_search",
                        session_string=sessions[0].get('session_string'),
                        api_id=config.get('api_id', 2040),
                        api_hash=config.get('api_hash', 'b18441a1ff607e10a989891a5462e627'),
                        proxy=proxy,
                        in_memory=True
                    )
                    await client.connect()
                    result = await OSINTEngine.search_phone(phone, client)
                    await client.disconnect()
                    return result
                
                result = asyncio.run(search_phone())
                
                if result["telegram_user"]:
                    u = result["telegram_user"]
                    print(f"  {C_SUCCESS}Найдено в Telegram:")
                    print(f"  {C_ACCENT}ID: {u['id']}")
                    print(f"  {C_ACCENT}Username: @{u['username']}")
                    print(f"  {C_ACCENT}Имя: {u['first_name']} {u['last_name']}")
                    print(f"  {C_ACCENT}Телефон: {u['phone']}")
                    print(f"  {C_ACCENT}Premium: {u['is_premium']}")
                    print(f"  {C_ACCENT}Scam: {u['is_scam']}")
                else:
                    print(f"  {C_WARNING}Не найдено в Telegram")
                
                if result["errors"]:
                    for err in result["errors"]:
                        print(f"  {C_ERROR}{err}")
        
        # ========== 3. Поиск по ID ==========
        elif choice == '3':
            uid = self.get_user_input("ID пользователя", "", "str")
            if uid is None or not uid:
                return "main_menu"
            
            try:
                uid = int(uid)
            except ValueError:
                print(f"  {C_ERROR}Неверный ID")
                self.get_user_input("Нажмите Enter", "", "str")
                return "main_menu"
            
            self.print_separator()
            print()
            print(f"  {C_TEXT}Ищем ID {C_BRIGHT}{uid}{C_TEXT}...")
            print()
            
            from session_manager import SessionManager
            sm = SessionManager()
            sessions = sm.get_cached_sessions()
            
            if not sessions:
                print(f"  {C_ERROR}Нет активных сессий.")
            else:
                from pyrogram import Client
                from proxy_manager import ProxyManager
                import random
                config = self.config_manager.load_config()
                
                pm = ProxyManager()
                proxy = random.choice(pm.proxies) if pm.proxies else None
                
                if proxy:
                    print(f"  {C_ACCENT}Использую прокси: {proxy.get('hostname')}:{proxy.get('port')}")
                
                async def search_id():
                    client = Client(
                        name="osint_id",
                        session_string=sessions[0].get('session_string'),
                        api_id=config.get('api_id', 2040),
                        api_hash=config.get('api_hash', 'b18441a1ff607e10a989891a5462e627'),
                        proxy=proxy,
                        in_memory=True
                    )
                    await client.connect()
                    result = await OSINTEngine.search_id(uid, client)
                    await client.disconnect()
                    return result
                
                result = asyncio.run(search_id())
                
                if result["user_info"]:
                    u = result["user_info"]
                    print(f"  {C_SUCCESS}Найдено в Telegram:")
                    print(f"  {C_ACCENT}ID: {u['id']}")
                    print(f"  {C_ACCENT}Username: @{u['username']}")
                    print(f"  {C_ACCENT}Имя: {u['first_name']} {u['last_name']}")
                    print(f"  {C_ACCENT}Телефон: {u['phone']}")
                    print(f"  {C_ACCENT}Premium: {u['is_premium']}")
                    print(f"  {C_ACCENT}Verified: {u['is_verified']}")
                    print(f"  {C_ACCENT}Scam: {u['is_scam']}")
                    print(f"  {C_ACCENT}Bot: {u['is_bot']}")
                else:
                    print(f"  {C_WARNING}Не найдено")
        
                if result["errors"]:
                    for err in result["errors"]:
                        print(f"  {C_ERROR}{err}")
        
        # ========== 4. Поиск email в утечках ==========
        elif choice == '4':
            email = self.get_user_input("Email", "", "str")
            if email is None or not email:
                return "main_menu"
            
            self.print_separator()
            print()
            print(f"  {C_TEXT}Проверяем {C_BRIGHT}{email}{C_TEXT} на утечки...")
            print()
            
            result = OSINTEngine.search_email(email)
            
            if result["breaches"]:
                print(f"  {C_SUCCESS}Найдено утечек: {len(result['breaches'])}")
                for b in result["breaches"][:10]:
                    print(f"  {C_ERROR}[!] {C_ACCENT}{b['name']} ({b['date']})")
            else:
                print(f"  {C_SUCCESS}Утечек не найдено")
            
            if result["errors"]:
                for err in result["errors"]:
                    print(f"  {C_ERROR}{err}")
        
        # ========== 5. LeakCheck ==========
        elif choice == '5':
            print(f"\n  {C_TEXT}Поиск в слитых базах (LeakCheck):")
            print(f"  {C_ACCENT}[1] По email")
            print(f"  {C_ACCENT}[2] По username")
            print()
            
            sub = self.get_user_input("Тип поиска", "1", "str")
            query = self.get_user_input("Запрос", "", "str")
            
            if query is None or not query:
                return "main_menu"
            
            qtype = "email" if sub == "1" else "username"
            
            self.print_separator()
            print()
            print(f"  {C_TEXT}Ищем {C_BRIGHT}{query}{C_TEXT} в утечках...")
            print()
            
            result = OSINTEngine.search_leakcheck(query, qtype)
            
            if result["sources"]:
                print(f"  {C_SUCCESS}Найдено утечек: {result.get('found', len(result['sources']))}")
                if result.get("fields"):
                    print(f"  {C_ACCENT}Утекшие данные: {', '.join(result['fields'])}")
                print()
                for s in result["sources"]:
                    print(f"  {C_ERROR}[!] {C_ACCENT}{s['name']} ({s['date']})")
            else:
                print(f"  {C_WARNING}Ничего не найдено")
            
            if result["errors"]:
                for err in result["errors"]:
                    print(f"  {C_ERROR}{err}")
        
        print()
        self.get_user_input("Нажмите Enter для возврата", "", "str")
        return "main_menu"
    
    def menu_exit(self) -> str:
        """Выход из VLXDIS."""
        self.print_header()
        print(f"{C_ERROR}  VLXDIS | ВЫХОД")
        self.print_separator()
        print()
        
        confirm = self.get_user_input("Сохранить текущую конфигурацию перед выходом? (y/n)", "y", "choice")
        if confirm == 'y':
            self.config_manager.save_config(self.current_config)
            print(f"{C_SUCCESS}[VLXDIS] Конфигурация сохранена")
        
        print(f"{C_ACCENT}[VLXDIS] Завершение работы... Build: {BUILD_DATE}")
        print(f"{C_ACCENT}[VLXDIS] Контакт: {TELEGRAM_CONTACT}")
        time.sleep(1)
        return "exit"
    
    def run(self):
        """Запуск главного цикла меню VLXDIS."""
        try:
            print("[DEBUG] Entering main loop...")
            while True:
                print("[DEBUG] Calling show_main_menu...")
                result = self.show_main_menu()
                print(f"[DEBUG] show_main_menu returned: {result}")
                if result == "exit":
                    print("[DEBUG] Exit requested, breaking loop")
                    break
        except KeyboardInterrupt:
            print(f"\n{C_ACCENT}[VLXDIS] Forced exit")
        except Exception as e:
            print(f"[DEBUG] Exception in run: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"{C_ACCENT}  VLXDIS v{VERSION} finished. Build: {BUILD_DATE}")
            print(f"{C_ACCENT}  Telegram: {TELEGRAM_CONTACT}")
            sys.exit(0)


# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    import traceback
    try:
        os.makedirs("history", exist_ok=True)
        os.makedirs("history/reports", exist_ok=True)
        os.makedirs("configs", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        required_files = {
            "accounts.txt": f"# VLXDIS\n+79XXXXXXXXX\n",
            "session_strings.txt": f"# VLXDIS\n",
            "socks5_proxies.txt": f"# VLXDIS\n",
            CONFIG_FILE: json.dumps({
                "api_id": 2040,
                "api_hash": "b18441a1ff607e10a989891a5462e627",
                "max_snos_time": 120,
                "auto_save": True,
                "logging": True,
                "dev_mode": False,
                "version": VERSION,
                "build_date": BUILD_DATE,
                "software": "VLXDIS",
                "telegram_contact": TELEGRAM_CONTACT
            }, indent=4)
        }
        
        for filename, default_content in required_files.items():
            if not os.path.exists(filename):
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(default_content)
        
        print(f"\n{C_FRAME}╔══════════════════════════════════════════════════════════╗")
        print(f"{C_FRAME}║  {C_TEXT}VLXDIS v{VERSION}{C_FRAME}                                          ║")
        print(f"{C_FRAME}║  {C_ACCENT}Telegram Account Snoser{C_FRAME}                              ║")
        print(f"{C_FRAME}║  {C_TEXT}Build: {BUILD_DATE}{C_FRAME}                                      ║")
        print(f"{C_FRAME}║  {C_TEXT}Telegram: {C_BRIGHT}{TELEGRAM_CONTACT}{C_FRAME}                            ║")
        print(f"{C_FRAME}╚══════════════════════════════════════════════════════════╝\n")
        
        print("[DEBUG] Creating InteractiveMenu...")
        menu = InteractiveMenu()
        print("[DEBUG] Starting menu.run()...")
        menu.run()
        
    except Exception as e:
        print(f"\n[C] ERROR: {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...")