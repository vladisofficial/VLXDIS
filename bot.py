#!/usr/bin/env python3
# bot.py
# VLXDIS Telegram Bot v1.6.0
# Build: 26.05.2026
# Telegram: @Itz_Vladis

import os
import json
import asyncio
from datetime import datetime
from typing import Dict
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from telegram.constants import ParseMode

from report_engine import ReportEngine
from config_manager import ConfigManager
from history_manager import HistoryManager
from session_manager import SessionManager
from proxy_manager import ProxyManager

# ========== КОНСТАНТЫ ==========
VERSION = "1.6.0"
BUILD_DATE = "26.05.2026"
BOT_TOKEN = "ВСТАВЬ_ТОКЕН"

# Состояния
(TARGET, REPORT_TYPES, COUNT, CONCURRENT, MESSAGE, DELAY_MIN, DELAY_MAX, CONFIRM) = range(8)
(SESS_PHONE) = range(1)
(PROXY_STRING) = range(1)

# Значения задержек
DELAY_VALUES = ["0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5"]

# Активные сносы
active_snoses: Dict[int, Dict] = {}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_managers():
    return ConfigManager(), HistoryManager(), SessionManager(), ProxyManager()

def get_config():
    return ConfigManager().load_config()

def save_config(config):
    ConfigManager().save_config(config)

def check_admin(user_id):
    config = get_config()
    admins = config.get("bot_admin_ids", [])
    supers = config.get("bot_super_admins", [])
    if not admins and not supers:
        return True
    return user_id in admins or user_id in supers

def check_super(user_id):
    config = get_config()
    supers = config.get("bot_super_admins", [])
    if not supers:
        return True
    return user_id in supers

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def build_delay_keyboard():
    """Создаёт клавиатуру для выбора задержки."""
    buttons = []
    row = []
    for i, val in enumerate(DELAY_VALUES):
        row.append(InlineKeyboardButton(val, callback_data=f"delay_{val}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"VLXDIS Bot v{VERSION}\n"
        f"Build: {BUILD_DATE}\n\n"
        "/snos — Start new snos\n"
        "/status — Active snos status\n"
        "/stop — Stop active snos\n"
        "/stats — Statistics\n"
        "/sessions — Show sessions\n"
        "/addsession — Add new session\n"
        "/proxies — Show proxies\n"
        "/addproxy — Add proxy\n"
        "/config — Show config\n"
        "/help — All commands"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "VLXDIS Commands:\n\n"
        "/snos — Start new report campaign\n"
        "/status — Check active snos\n"
        "/stop — Stop active snos\n"
        "/stats — Show statistics\n"
        "/sessions — Show sessions\n"
        "/addsession — Add session by phone or string\n"
        "/proxies — Show proxies\n"
        "/addproxy — Add proxy\n"
        "/config — Show config\n\n"
        "Admin commands:\n"
        "/addadmin ID — Add admin\n"
        "/adduser @name — Add admin by username\n"
        "/removeadmin ID — Remove admin\n"
        "/adminlist — Show admins\n"
        "/setsuper ID — Set super admin\n"
        "/removesuper ID — Remove super admin"
    )

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in active_snoses:
        await update.message.reply_text("No active snos. Start with /snos")
        return
    
    data = active_snoses[user_id]
    engine = data['engine']
    stats = engine.get_stats()
    elapsed = datetime.now().timestamp() - stats['start_time']
    progress = (stats['total_sent'] / engine.report_count * 100) if engine.report_count > 0 else 0
    
    text = (
        f"Snos Status\n\n"
        f"Target: {engine.target}\n"
        f"Progress: {stats['total_sent']}/{engine.report_count} ({progress:.1f}%)\n"
        f"Success: {stats['successful']}\n"
        f"Errors: {stats['failed']}\n"
        f"Flood waits: {stats['flood_limited']}\n"
        f"Time: {format_time(elapsed)}\n"
        f"Speed: {stats['total_sent']/elapsed:.1f}/sec\n\n"
    )
    
    if engine.is_campaign_finished():
        text += "Status: COMPLETED"
        if user_id in active_snoses:
            del active_snoses[user_id]
    else:
        text += "Status: RUNNING"
    
    await update.message.reply_text(text)

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in active_snoses:
        await update.message.reply_text("No active snos.")
        return
    
    del active_snoses[user_id]
    await update.message.reply_text("Snos stopped.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, history_manager, session_manager, proxy_manager = get_managers()
    history = history_manager.get_all_records()
    total = sum(r.get('reports_sent', 0) for r in history)
    success = sum(r.get('successful', 0) for r in history)
    completed = sum(1 for r in history if r.get('status') == 'COMPLETED')
    
    text = (
        f"Statistics\n\n"
        f"Snoses: {len(history)}\n"
        f"Completed: {completed}\n"
        f"Reports: {total}\n"
        f"Successful: {success}\n"
        f"Rate: {(success/total*100) if total > 0 else 0:.1f}%\n\n"
        f"Sessions: {len(session_manager.get_cached_sessions())}\n"
        f"Proxies: {len(proxy_manager.proxies)}\n"
        f"Active snoses: {len(active_snoses)}"
    )
    await update.message.reply_text(text)

async def sessions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, _, sm, _ = get_managers()
    sessions = sm.get_cached_sessions()
    
    if not sessions:
        await update.message.reply_text("No sessions. Use /addsession to add.")
        return
    
    text = f"Sessions ({len(sessions)})\n\n"
    for i, s in enumerate(sessions[:15], 1):
        text += f"{i}. {s.get('phone', '?')} | Active: {s.get('is_active', False)}\n"
    if len(sessions) > 15:
        text += f"\n... +{len(sessions)-15}"
    
    await update.message.reply_text(text)

async def proxies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, _, _, pm = get_managers()
    proxies = pm.proxies
    
    if not proxies:
        await update.message.reply_text("No proxies. Use /addproxy to add.")
        return
    
    text = f"Proxies ({len(proxies)})\n\n"
    for i, p in enumerate(proxies[:15], 1):
        text += f"{i}. {p.get('hostname')}:{p.get('port')}\n"
    if len(proxies) > 15:
        text += f"\n... +{len(proxies)-15}"
    
    await update.message.reply_text(text)

async def config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = get_config()
    text = (
        f"Config\n\n"
        f"API ID: {config.get('api_id', '?')}\n"
        f"API Hash: {config.get('api_hash', '?')[:8]}...\n"
        f"Max time: {config.get('max_snos_time', '?')} min\n"
        f"Auto save: {config.get('auto_save', False)}\n"
        f"Version: {config.get('version', '?')}\n"
        f"Build: {config.get('build_date', '?')}"
    )
    await update.message.reply_text(text)

# ========== ДОБАВЛЕНИЕ СЕССИЙ ==========
async def addsession_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("Denied.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Add session:\n\n"
        "1. Send phone number (+79123456789) to create new session\n"
        "2. Or send existing session string to add directly\n\n"
        "/cancel to abort"
    )
    return SESS_PHONE

async def addsession_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    _, _, sm, _ = get_managers()
    
    if text.startswith('+') or (text.isdigit() and len(text) >= 10):
        phone = text if text.startswith('+') else f"+{text}"
        await update.message.reply_text(f"Creating session for {phone}...")
        
        try:
            session = await sm.create_session(phone)
            if session:
                await update.message.reply_text(f"Session for {phone} created and saved!")
            else:
                await update.message.reply_text("Failed to create session.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
    else:
        sm.add_session(text, phone=f"manual_{len(sm.get_cached_sessions())+1}")
        
        with open("session_strings.txt", "a", encoding="utf-8") as f:
            f.write(text + "\n")
        
        await update.message.reply_text("Session added from string!")
    
    return ConversationHandler.END

async def addsession_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

# ========== ДОБАВЛЕНИЕ ПРОКСИ ==========
async def addproxy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("Denied.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Add proxy:\n\n"
        "Send proxy in format:\n"
        "ip:port:username:password\n"
        "or\n"
        "ip:port\n\n"
        "/cancel to abort"
    )
    return PROXY_STRING

async def addproxy_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    _, _, _, pm = get_managers()
    
    if pm.add_proxy(text):
        await update.message.reply_text(f"Proxy added: {text}")
    else:
        await update.message.reply_text("Invalid format.")
    
    return ConversationHandler.END

async def addproxy_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

# ========== АДМИНИСТРИРОВАНИЕ ==========
async def add_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_super(update.effective_user.id):
        await update.message.reply_text("Denied. Super admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("/addadmin USER_ID")
        return
    
    try:
        new_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID.")
        return
    
    config = get_config()
    admins = config.get("bot_admin_ids", [])
    
    if new_id in admins:
        await update.message.reply_text(f"{new_id} already admin.")
        return
    
    admins.append(new_id)
    config["bot_admin_ids"] = admins
    save_config(config)
    await update.message.reply_text(f"Admin added: {new_id}")

async def add_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_super(update.effective_user.id):
        await update.message.reply_text("Denied. Super admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("/adduser @username")
        return
    
    username = context.args[0].strip().lstrip('@')
    config = get_config()
    usernames = config.get("bot_admin_usernames", [])
    
    if username.lower() in [u.lower() for u in usernames]:
        await update.message.reply_text(f"@{username} already admin.")
        return
    
    usernames.append(username)
    config["bot_admin_usernames"] = usernames
    save_config(config)
    await update.message.reply_text(f"Admin added: @{username}\nThey need to send /start to activate.")

async def remove_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_super(update.effective_user.id):
        await update.message.reply_text("Denied.")
        return
    
    if not context.args:
        await update.message.reply_text("/removeadmin USER_ID")
        return
    
    try:
        rem_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID.")
        return
    
    config = get_config()
    admins = config.get("bot_admin_ids", [])
    supers = config.get("bot_super_admins", [])
    
    if rem_id in supers:
        await update.message.reply_text("Cannot remove super admin.")
        return
    
    if rem_id not in admins:
        await update.message.reply_text("Not admin.")
        return
    
    admins.remove(rem_id)
    config["bot_admin_ids"] = admins
    save_config(config)
    await update.message.reply_text(f"Admin removed: {rem_id}")

async def admin_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("Denied.")
        return
    
    config = get_config()
    supers = config.get("bot_super_admins", [])
    admins = config.get("bot_admin_ids", [])
    usernames = config.get("bot_admin_usernames", [])
    
    text = "Admins\n\n"
    
    if supers:
        text += "Super admins:\n"
        for uid in supers:
            text += f"- {uid}\n"
        text += "\n"
    
    if admins:
        text += "Admins:\n"
        for uid in admins:
            text += f"- {uid}\n"
        text += "\n"
    
    if usernames:
        text += "By username:\n"
        for u in usernames:
            text += f"- @{u}\n"
    
    if not admins and not usernames and not supers:
        text += "No admins.\n"
    
    await update.message.reply_text(text)

async def set_super_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_super(update.effective_user.id):
        await update.message.reply_text("Denied.")
        return
    
    if not context.args:
        await update.message.reply_text("/setsuper USER_ID")
        return
    
    try:
        new_super = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID.")
        return
    
    config = get_config()
    supers = config.get("bot_super_admins", [])
    
    if new_super in supers:
        await update.message.reply_text(f"{new_super} already super admin.")
        return
    
    supers.append(new_super)
    config["bot_super_admins"] = supers
    save_config(config)
    await update.message.reply_text(f"Super admin set: {new_super}")

async def remove_super_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_super(update.effective_user.id):
        await update.message.reply_text("Denied.")
        return
    
    if not context.args:
        await update.message.reply_text("/removesuper USER_ID")
        return
    
    try:
        rem_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID.")
        return
    
    config = get_config()
    supers = config.get("bot_super_admins", [])
    
    if rem_id not in supers:
        await update.message.reply_text("Not super admin.")
        return
    
    if len(supers) <= 1:
        await update.message.reply_text("Cannot remove last super admin.")
        return
    
    supers.remove(rem_id)
    config["bot_super_admins"] = supers
    save_config(config)
    await update.message.reply_text(f"Super admin removed: {rem_id}")

# ========== СНОС ==========
async def snos_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return ConversationHandler.END
    
    _, _, sm, _ = get_managers()
    if not sm.get_cached_sessions():
        await update.message.reply_text("No sessions. Use /addsession first.")
        return ConversationHandler.END
    
    context.user_data.clear()
    
    await update.message.reply_text("Enter target:\n@username / +phone / ID\n\n/cancel to abort")
    return TARGET

async def snos_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target'] = update.message.text.strip()
    
    keyboard = [
        [InlineKeyboardButton("SPAM", callback_data="t_1"),
         InlineKeyboardButton("VIOLENCE", callback_data="t_2")],
        [InlineKeyboardButton("PORNOGRAPHY", callback_data="t_3"),
         InlineKeyboardButton("CHILD ABUSE", callback_data="t_4")],
        [InlineKeyboardButton("COPYRIGHT", callback_data="t_5"),
         InlineKeyboardButton("OTHER", callback_data="t_6")],
        [InlineKeyboardButton("ALL", callback_data="t_all")],
    ]
    
    await update.message.reply_text(
        f"Target: {context.user_data['target']}\nSelect type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REPORT_TYPES

async def snos_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    type_map = {
        "t_1": ["inputReportReasonSpam"],
        "t_2": ["inputReportReasonViolence"],
        "t_3": ["inputReportReasonPornography"],
        "t_4": ["inputReportReasonChildAbuse"],
        "t_5": ["inputReportReasonCopyright"],
        "t_6": ["inputReportReasonOther"],
        "t_all": ["inputReportReasonSpam", "inputReportReasonViolence",
                  "inputReportReasonPornography", "inputReportReasonChildAbuse",
                  "inputReportReasonCopyright", "inputReportReasonOther"]
    }
    names = {"t_1": "SPAM", "t_2": "VIOLENCE", "t_3": "PORNOGRAPHY",
             "t_4": "CHILD ABUSE", "t_5": "COPYRIGHT", "t_6": "OTHER", "t_all": "ALL"}
    
    context.user_data['types'] = type_map.get(query.data, type_map["t_all"])
    await query.edit_message_text(f"Type: {names.get(query.data, 'ALL')}\n\nEnter count (1-5000):")
    return COUNT

async def snos_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cnt = int(update.message.text)
        if cnt < 1 or cnt > 5000:
            raise ValueError
        context.user_data['count'] = cnt
    except ValueError:
        await update.message.reply_text("1-5000:")
        return COUNT
    
    sessions = len(SessionManager().get_cached_sessions())
    await update.message.reply_text(f"Count: {cnt}\nSessions: {sessions}\n\nConcurrent (1-{sessions}):")
    return CONCURRENT

async def snos_concurrent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['concurrent'] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Number:")
        return CONCURRENT
    
    await update.message.reply_text("Message (or /default):")
    return MESSAGE

async def snos_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip() if update.message.text else ''
    
    if msg == '/default' or msg == '':
        msg = "This account violates Telegram Terms of Service."
    
    context.user_data['message'] = msg
    
    await update.message.reply_text(
        "Select minimum delay:",
        reply_markup=build_delay_keyboard()
    )
    return DELAY_MIN

async def snos_delay_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    min_val = float(query.data.replace("delay_", ""))
    context.user_data['delay_min'] = min_val
    
    await query.edit_message_text(
        f"Min delay: {min_val}s\n\nSelect maximum delay:",
        reply_markup=build_delay_keyboard()
    )
    return DELAY_MAX

async def snos_delay_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    max_val = float(query.data.replace("delay_", ""))
    
    if max_val < context.user_data.get('delay_min', 0):
        await query.answer(f"Must be >= {context.user_data.get('delay_min')}s", show_alert=True)
        return DELAY_MAX
    
    context.user_data['delay_max'] = max_val
    
    d = context.user_data
    text = (
        f"Confirm\n\n"
        f"Target: {d.get('target')}\n"
        f"Count: {d.get('count')}\n"
        f"Sessions: {d.get('concurrent')}\n"
        f"Delay: {d.get('delay_min')}-{d.get('delay_max')}s\n\n"
        f"/go — Start\n/cancel — Abort"
    )
    await query.edit_message_text(text)
    return CONFIRM

async def snos_go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != '/go':
        await update.message.reply_text("Send /go or /cancel")
        return CONFIRM
    
    user_id = update.effective_user.id
    d = context.user_data
    _, _, sm, pm = get_managers()
    
    config = {
        "target": d.get('target'),
        "report_types": d.get('types'),
        "report_count": d.get('count'),
        "concurrent_sessions": d.get('concurrent'),
        "report_message": d.get('message'),
        "delay_range": (d.get('delay_min', 0.5), d.get('delay_max', 2.0)),
        "timestamp": datetime.now().isoformat(),
        "session_pool": sm.get_cached_sessions(),
        "proxy_list": pm.proxies,
        "telegram_contact": "@Itz_Vladis",
        "software": "VLXDIS",
        "version": VERSION
    }
    
    engine = ReportEngine(config)
    
    msg = await update.message.reply_text("Snos started. Use /status to check progress.")
    
    active_snoses[user_id] = {
        'engine': engine,
        'msg': msg,
        'update': update,
        'target': config['target']
    }
    
    async def background():
        try:
            await engine.run_report_campaign()
        except Exception as e:
            print(f"Background error: {e}")
        
        stats = engine.get_stats()
        elapsed = datetime.now().timestamp() - stats['start_time']
        
        final_text = (
            f"Snos completed!\n\n"
            f"Target: {config['target']}\n"
            f"Sent: {stats['total_sent']}\n"
            f"Success: {stats['successful']}\n"
            f"Errors: {stats['failed']}\n"
            f"Floods: {stats['flood_limited']}\n"
            f"Time: {format_time(elapsed)}\n\n"
            f"/snos — new\n/status — stats"
        )
        
        try:
            await msg.edit_text(final_text)
        except:
            await update.message.reply_text(final_text)
            
        if user_id in active_snoses:
            del active_snoses[user_id]
    
    context.job_queue.run_once(lambda ctx: asyncio.create_task(background()), 0)
    
    return ConversationHandler.END

async def snos_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. /snos to start again.")
    return ConversationHandler.END

# ========== ЗАПУСК ==========
def main():
    os.makedirs("history", exist_ok=True)
    os.makedirs("history/reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print(f"VLXDIS Bot v{VERSION}")
    print(f"Build: {BUILD_DATE}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Основные
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("sessions", sessions_cmd))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(CommandHandler("config", config_cmd))
    
    # Добавление сессий
    addsession_conv = ConversationHandler(
        entry_points=[CommandHandler("addsession", addsession_start)],
        states={
            SESS_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addsession_process)],
        },
        fallbacks=[CommandHandler("cancel", addsession_cancel)],
    )
    app.add_handler(addsession_conv)
    
    # Добавление прокси
    addproxy_conv = ConversationHandler(
        entry_points=[CommandHandler("addproxy", addproxy_start)],
        states={
            PROXY_STRING: [MessageHandler(filters.TEXT & ~filters.COMMAND, addproxy_process)],
        },
        fallbacks=[CommandHandler("cancel", addproxy_cancel)],
    )
    app.add_handler(addproxy_conv)
    
    # Админ
    app.add_handler(CommandHandler("addadmin", add_admin_cmd))
    app.add_handler(CommandHandler("adduser", add_user_cmd))
    app.add_handler(CommandHandler("removeadmin", remove_admin_cmd))
    app.add_handler(CommandHandler("adminlist", admin_list_cmd))
    app.add_handler(CommandHandler("setsuper", set_super_cmd))
    app.add_handler(CommandHandler("removesuper", remove_super_cmd))
    
    # Снос
    snos_conv = ConversationHandler(
        entry_points=[CommandHandler("snos", snos_start)],
        states={
            TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, snos_target)],
            REPORT_TYPES: [CallbackQueryHandler(snos_types)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, snos_count)],
            CONCURRENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, snos_concurrent)],
            MESSAGE: [MessageHandler(filters.TEXT, snos_message)],
            DELAY_MIN: [CallbackQueryHandler(snos_delay_min)],
            DELAY_MAX: [CallbackQueryHandler(snos_delay_max)],
            CONFIRM: [MessageHandler(filters.TEXT, snos_go)],
        },
        fallbacks=[CommandHandler("cancel", snos_cancel)],
        per_message=False
    )
    app.add_handler(snos_conv)
    
    print("=" * 50)
    print("Bot is running.")
    print("=" * 50)
    
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("\nBot stopped.")
    finally:
        print(f"VLXDIS Bot v{VERSION} finished.")

if __name__ == "__main__":
    main()