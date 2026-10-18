from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import SendReactionRequest, GetMessagesViewsRequest
from telethon.tl.types import ReactionEmoji, ReactionCustomEmoji
import os
import asyncio
import random
import shutil
import psutil
import time
import socket
import urllib.request
from datetime import datetime, timezone
from typing import List

app = FastAPI()

api_id = 39286516
api_hash = '9f5cedcd688bbaade3398c8c8c30f2b8'

SESSION_DIR = "/home/kaliaza/telegram_panel_pc"
BACKUP_DIR = "/home/kaliaza/telegram_panel_pc/backups"
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

account_cache = {}
task_history = []

task_state = {
    "is_running": False,
    "total": 0,
    "current": 0,
    "success": 0,
    "failed": 0,
    "start_time": 0,
    "info": ""
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_external_ip():
    try:
        return urllib.request.urlopen('https://ifconfig.me/ip', timeout=2).read().decode('utf8')
    except:
        return "Aniqlanmadi"

def randomize_message(original_text: str) -> str:
    emojis = ["✨", "🚀", "🔥", "💡", "🎯", "⭐", "🔹", "📌", "✅", "⚡", "💎", "🌐"]
    greetings = ["Salom!", "Assalomu alaykum!", "Hey!", "Salom do'st!", "Barchaga salom!", "Assalom!"]
    return f"{random.choice(greetings)} {original_text} {random.choice(emojis)}"

@app.get("/api/stats")
async def get_stats():
    process = psutil.Process(os.getpid())
    app_memory_mb = round(process.memory_info().rss / (1024 * 1024), 2)
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "ram_used": round(psutil.virtual_memory().used / (1024 ** 3), 2),
        "ram_total": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "disk_percent": round((shutil.disk_usage("/").used / shutil.disk_usage("/").total) * 100, 1),
        "disk_free": round(shutil.disk_usage("/").free / (1024 ** 3), 2),
        "app_ram": app_memory_mb,
        "local_ip": get_local_ip(),
        "external_ip": get_external_ip()
    }

@app.get("/api/progress")
async def get_progress():
    if not task_state["is_running"]:
        return {"is_running": False}
    total, current = task_state["total"], task_state["current"]
    percent = round((current / total) * 100, 1) if total > 0 else 0
    elapsed = int(time.time() - task_state["start_time"])
    return {**task_state, "percent": percent, "elapsed": elapsed}

@app.get("/api/scan-reactions")
async def scan_reactions(target: str):
    all_files = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    if not all_files:
        return JSONResponse({"error": "Aktiv sessiya topilmadi!"})
    
    client = TelegramClient(os.path.join(SESSION_DIR, all_files[0].replace('.session', '')), api_id, api_hash, request_retries=3, connection_retries=3)
    reactions_list = []
    try:
        await client.connect()
        entity_raw = target.strip()
        msg_id = None
        
        if entity_raw.startswith("https://t.me/"):
            if "/c/" in entity_raw:
                parts = entity_raw.split("/")
                channel_id = int("-100" + parts[parts.index("c") + 1])
                msg_id = int(parts[-1])
                entity = await client.get_entity(channel_id)
            else:
                clean_link = entity_raw.split("https://t.me/")[-1].strip("/")
                if "/" in clean_link:
                    parts = clean_link.split("/")
                    entity = await client.get_entity("@" + parts[0])
                    msg_id = int(parts[1])
                else:
                    entity = await client.get_entity("@" + clean_link)
        else:
            entity = await client.get_entity(entity_raw)

        target_msg = None
        if msg_id:
            async for m in client.iter_messages(entity, ids=msg_id):
                target_msg = m
                break
        else:
            async for m in client.iter_messages(entity, limit=1):
                target_msg = m
                break

        if target_msg and target_msg.reactions and target_msg.reactions.results:
            for r in target_msg.reactions.results:
                reaction_obj = r.reaction
                if isinstance(reaction_obj, ReactionEmoji):
                    reactions_list.append({"type": "emoji", "val": reaction_obj.emoticon})
                elif isinstance(reaction_obj, ReactionCustomEmoji):
                    reactions_list.append({"type": "custom", "val": str(reaction_obj.document_id)})
        
        await client.disconnect()
    except Exception as e:
        pass

    if not reactions_list:
        reactions_list = [
            {"type": "emoji", "val": "🔥"},
            {"type": "emoji", "val": "👍"},
            {"type": "emoji", "val": "❤️"},
            {"type": "emoji", "val": "👏"},
            {"type": "emoji", "val": "😁"},
            {"type": "emoji", "val": "🎉"},
            {"type": "emoji", "val": "⚡"},
            {"type": "emoji", "val": "🏆"}
        ]

    return {"reactions": reactions_list}

@app.get("/", response_class=HTMLResponse)
async def home(msg: str = ""):
    all_files = sorted([f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session') and f.replace('.session', '').replace('+', '').isdigit()])
    backup_files = sorted([f.replace('.session', '') for f in os.listdir(BACKUP_DIR) if f.endswith('.session') and f.replace('.session', '').replace('+', '').isdigit()])
    
    groups = {}
    for i, ses in enumerate(all_files):
        g_num = (i // 10) + 1
        groups.setdefault(g_num, []).append(ses)

    Parser_count = len(all_files)
    backup_count = len(backup_files)

    html = f"""
    <html>
        <head>
            <title>Telegram Boshqaruv Paneli</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 15px; margin: 0; }}
                h2 {{ color: #38bdf8; margin-top: 5px; font-size: 18px; }}
                .window {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.4); overflow: hidden; }}
                .window-header {{ background: #1e3a8a; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #3b82f6; font-weight: bold; cursor: pointer; color: #eff6ff; font-size: 13px; }}
                .window-controls {{ display: flex; gap: 6px; align-items: center; }}
                .window-body {{ padding: 12px; background: #1e293b; }}
                details > summary {{ list-style: none; outline: none; }}
                details > summary::-webkit-details-marker {{ display: none; }}
                input, textarea, select {{ padding: 8px; margin: 4px 0; width: 100%; background: #0f172a; border: 1px solid #475569; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 12px; }}
                input:focus, textarea:focus, select:focus {{ border-color: #38bdf8; outline: none; }}
                button {{ padding: 9px 16px; background: #0284c7; border: none; color: white; cursor: pointer; border-radius: 6px; font-weight: bold; font-size: 12px; transition: background 0.2s; }}
                button:hover {{ background: #0369a1; }}
                .btn-blue {{ background: #2563eb; }}
                .btn-purple {{ background: #7c3aed; }}
                .btn-orange {{ background: #d97706; }}
                .btn-green {{ background: #16a34a; }}
                .btn-danger {{ background: #dc2626; padding: 4px 8px; font-size: 10px; border-radius: 4px; }}
                .btn-toggle {{ background: #d97706; padding: 3px 10px; font-size: 10px; border-radius: 12px; cursor: pointer; font-weight: bold; border: none; color: #fff; }}
                .btn-toggle.active {{ background: #16a34a; }}
                
                .task-tabs {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }}
                .task-tab {{ padding: 8px 14px; background: #0f172a; border: 2px solid #475569; color: #cbd5e1; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 12px; flex: 1; min-width: 90px; text-align: center; }}
                .task-tab.active {{ background: #2563eb; border-color: #60a5fa; color: #fff; }}

                .task-row {{ background: #0f172a; border: 1px solid #334155; padding: 10px; border-radius: 6px; margin-bottom: 8px; position: relative; }}
                .remove-task {{ position: absolute; top: 8px; right: 8px; background: #dc2626; color: #fff; border: none; padding: 2px 6px; font-size: 10px; border-radius: 4px; cursor: pointer; }}

                ul {{ list-style: none; padding: 0; margin: 0; }}
                li {{ background: #0f172a; margin: 5px 0; padding: 8px 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; border: 1px solid #334155; }}
                .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }}
                .badge-green {{ background: #166534; color: #dcfce7; }}
                .badge-red {{ background: #991b1b; color: #fee2e2; }}
                .badge-gray {{ background: #475569; color: #f1f5f9; }}
                .group-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 6px; margin-bottom: 8px; overflow: hidden; }}
                .group-header {{ background: #1e3a8a; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; color: #93c5fd; cursor: pointer; font-size: 12px; }}
                .group-body {{ padding: 10px; }}
                .group-checkboxes {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0; }}
                .group-checkboxes label {{ background: #0f172a; padding: 6px 10px; border-radius: 6px; cursor: pointer; border: 1px solid #475569; font-size: 12px; color: #e2e8f0; }}
                .ip-box {{ background: #1e3a8a; border: 1px solid #3b82f6; padding: 8px 14px; border-radius: 6px; margin-bottom: 12px; font-size: 12px; color: #e0f2fe; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 6px; align-items: center; }}
                .progress-box {{ background: #1e293b; border: 1px solid #f59e0b; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; display: none; }}
                .alert-box {{ background: #166534; color: #dcfce7; padding: 8px 14px; border-radius: 6px; margin-bottom: 12px; font-weight: bold; border: 1px solid #22c55e; display: flex; justify-content: space-between; align-items: center; font-size: 12px; }}
                .alert-close {{ background: transparent; border: none; color: #dcfce7; font-size: 14px; cursor: pointer; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h2>⚡ Telegram Boshqaruv Paneli ({Parser_count} ta Akkaunt)</h2>
            
            <div class="ip-box">
                <div>🌐 <b>IP:</b> <span id="ext-ip">Yuklanmoqda...</span> | 💻 <b>Lokal:</b> <span id="loc-ip">Yuklanmoqda...</span></div>
                <div id="ram-indicator" style="background: #2563eb; padding: 3px 8px; border-radius: 8px; font-size: 11px; font-weight: bold; color: #fff;">RAM: 0 MB</div>
            </div>
    """
    
    if msg:
        html += f'''
            <div class="alert-box" id="notification-banner">
                <span>🔔 {msg}</span>
                <button class="alert-close" onclick="document.getElementById('notification-banner').style.display='none'">✖</button>
            </div>
        '''

    html += f"""
            <!-- 1. ZADANIYA PANELI -->
            <div class="window" id="win-task">
                <details open ontoggle="handleToggle('win-task', this)">
                    <summary class="window-header" style="background: #0284c7;">
                        <span>🚀 Zadaniya Bajarish Paneli (5 tagacha)</span>
                        <div class="window-controls">
                            <button type="button" class="btn-toggle active" id="btn-win-task" onclick="event.stopPropagation(); toggleWindow('win-task')">ON</button>
                        </div>
                    </summary>
                    <div class="window-body">
                        <form action="/broadcast" method="post" onsubmit="startAction(event, '/broadcast')">
                            
                            <div id="tasks-container">
                                <div class="task-row" id="task-item-0" data-index="0">
                                    <b style="color: #38bdf8; font-size: 12px;">1-Zadaniya:</b>
                                    <div class="task-tabs" style="margin-top: 6px;">
                                        <button type="button" class="task-tab active" onclick="setTaskType(0, 'join', this)">📢 Obuna</button>
                                        <button type="button" class="task-tab" onclick="setTaskType(0, 'view', this)">👁️ Prosmotr</button>
                                        <button type="button" class="task-tab" onclick="setTaskType(0, 'msg', this)">💬 Xabar</button>
                                        <button type="button" class="task-tab" onclick="setTaskType(0, 'bot', this)">🤖 Bot</button>
                                        <button type="button" class="task-tab" onclick="setTaskType(0, 'react', this)">🔥 Emotsiya</button>
                                    </div>
                                    <input type="hidden" name="task_types" id="task_type_0" value="join">
                                    
                                    <input type="text" name="targets" id="target_0" placeholder="Kanal yoki post ssilkasi (Masalan: https://t.me/...)" required style="margin-top: 4px;">
                                    
                                    <div id="extra_container_0" style="display:none; margin-top:4px;">
                                        <input type="text" name="messages" id="msg_0" placeholder="Xabar matni yoki buyruq...">
                                    </div>

                                    <div id="reaction_container_0" style="display:none; margin-top:6px;">
                                        <button type="button" class="btn-purple" onclick="scanReactions(0)" style="font-size:11px; padding:6px 12px;">🔍 Emotsiyalarni Skaner Qilish</button>
                                        <div id="reaction_buttons_0" style="display:flex; gap:6px; margin-top:6px; flex-wrap:wrap;"></div>
                                        <input type="hidden" name="reactions" id="reaction_input_0" value="auto">
                                    </div>
                                </div>
                            </div>

                            <button type="button" class="btn-purple" onclick="addTaskRow()" style="margin-top: 6px; width: 100%; font-size: 12px; padding: 8px;">➕ Yana Zadaniya Qo'shish (Maks 5 ta)</button>

                            <div style="margin-top: 8px;">
                                <label style="font-size:11px; color:#fbbf24; font-weight:bold;">Himoya Rejimi:</label>
                                <select name="mode">
                                    <option value="fast">⚡ Tezkor Rejim</option>
                                    <option value="pro" selected>🛡️ Pro Rejimi (Xavfsiz va Aniq)</option>
                                </select>
                            </div>

                            <label style="font-size:11px; color:#38bdf8; font-weight:bold; margin-top:6px; display:block;">Guruhni tanlang:</label>
                            <div class="group-checkboxes">
    """
    for g_id in groups.keys():
        html += f"""
                                <label><input type="checkbox" name="selected_groups" value="{g_id}" checked> {g_id}-Guruh</label>
        """
    html += """
                            </div>
                            <button type="submit" class="btn-green" style="margin-top: 10px; width: 100%; padding: 12px; font-size: 14px;">🚀 Barcha Zadaniylarni Boshlash</button>
                        </form>
                    </div>
                </details>
            </div>

            <div id="live-progress-box" class="progress-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span id="prog-title" style="font-weight: bold; color: #fbbf24; font-size: 12px;">⏳ Bajarilmoqda...</span>
                    <span id="prog-time" style="font-size: 11px; color: #94a3b8;">0s</span>
                </div>
                <div style="background: #0f172a; border-radius: 4px; height: 6px; width: 100%; margin-bottom: 4px; overflow: hidden; border: 1px solid #334155;">
                    <div id="prog-bar" style="background: #fbbf24; height: 100%; width: 0%;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #cbd5e1;">
                    <span id="prog-counts">0 / 0</span>
                    <span id="prog-status">Jarayonda...</span>
                </div>
            </div>

            <!-- 2. SERVER ZAXIRA MARKAZI -->
            <div class="window" id="win-res">
                <details ontoggle="handleToggle('win-res', this)">
                    <summary class="window-header">
                        <span>🛡️ Zaxira Markazi ({backup_count} ta) & Fayl Yuklash</span>
                        <div class="window-controls">
                            <button type="button" class="btn-toggle" id="btn-win-res" onclick="event.stopPropagation(); toggleWindow('win-res')">OFF</button>
                        </div>
                    </summary>
                    <div class="window-body">
                        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                            <form action="/download-backup-zip" method="get" style="flex:1; margin:0;">
                                <button type="submit" class="btn-blue" style="width:100%; font-size:11px; padding:7px;">📦 ZIP Export</button>
                            </form>
                            <form action="/backup-sessions" method="post" style="flex:1; margin:0;">
                                <button type="submit" class="btn-purple" style="width:100%; font-size:11px; padding:7px;">🛡️ Zaxiralash</button>
                            </form>
                            <form action="/restore-sessions" method="post" style="flex:1; margin:0;" onsubmit="return confirm('Barcha akkauntlar tiklansinmi?');">
                                <button type="submit" class="btn-orange" style="width:100%; font-size:11px; padding:7px;">♻️ Restore</button>
                            </form>
                        </div>
                        <form action="/upload-session" method="post" enctype="multipart/form-data" style="margin-top:8px; display:flex; gap:6px;">
                            <input type="file" name="session_file" accept=".session" required style="font-size:11px; padding:4px; margin:0;">
                            <button type="submit" class="btn-orange" style="font-size:11px; padding:5px 10px;">Yuklash & Tiklash</button>
                        </form>
                    </div>
                </details>
            </div>

            <!-- 3. GURUHGA YANGI RAQAM QO'SHISH -->
            <div class="window" id="win-add-acc">
                <details ontoggle="handleToggle('win-add-acc', this)">
                    <summary class="window-header" style="background: #14532d; border-bottom: 1px solid #22c55e;">
                        <span style="color: #4ade80;">➕ Yangi Raqam Qo'shish (2-Oyna)</span>
                        <div class="window-controls">
                            <button type="button" class="btn-toggle" id="btn-win-add-acc" onclick="event.stopPropagation(); toggleWindow('win-add-acc')">OFF</button>
                        </div>
                    </summary>
                    <div class="window-body">
                        <a href="http://127.0.0.1:8001" target="_blank" class="btn-purple" style="padding: 7px 14px; text-decoration: none; display: inline-block; font-size: 12px;">🚀 Alohida Oynani Ochish</a>
                    </div>
                </details>
            </div>

            <!-- 4. BARCHA AKKAUNTLAR -->
            <div class="window" id="win-accounts">
                <details ontoggle="handleToggle('win-accounts', this)">
                    <summary class="window-header">
                        <span>📂 Ulangan Akkauntlar ({Parser_count} ta)</span>
                        <div class="window-controls">
                            <button type="button" class="btn-toggle" id="btn-win-accounts" onclick="event.stopPropagation(); toggleWindow('win-accounts')">OFF</button>
                        </div>
                    </summary>
                    <div class="window-body">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 6px; flex-wrap: wrap;">
                            <input type="text" id="searchInput" onkeyup="filterAccounts()" placeholder="🔍 Qidirish..." style="margin: 0; max-width: 220px;">
                            <div style="display: flex; gap: 5px;">
                                <form action="/check-accounts-fast" method="post" onsubmit="startAction(event, '/check-accounts-fast')" style="margin:0;">
                                    <button type="submit" class="btn-blue" style="padding: 5px 8px; font-size: 10px;">⚡ Tezkor</button>
                                </form>
                                <form action="/check-accounts" method="post" onsubmit="startAction(event, '/check-accounts')" style="margin:0;">
                                    <button type="submit" class="btn-orange" style="padding: 5px 8px; font-size: 10px;">🔄 To'liq</button>
                                </form>
                            </div>
                        </div>
    """

    for g_id, g_accounts in groups.items():
        html += f"""
                        <div class="group-card">
                            <details open>
                                <summary class="group-header">
                                    <span>📂 {g_id}-Guruh — {len(g_accounts)} ta raqam</span>
                                </summary>
                                <div class="group-body">
                                    <ul>
        """
        for ses in g_accounts:
            c_info = account_cache.get(ses, {"status": "Tekshirilmagan", "cls": "badge-gray"})
            html += f"""
                                        <li class="acc-item" data-text="{ses}">
                                            <span style="font-size: 12px; color: #38bdf8; font-weight: bold;">+{ses}</span>
                                            <div style="display: flex; gap: 5px; align-items: center;">
                                                <span class="badge {c_info['cls']}">{c_info['status']}</span>
                                                <form action="/restore-single" method="post" style="margin:0;">
                                                    <input type="hidden" name="phone" value="{ses}">
                                                    <button type="submit" class="btn-orange" style="padding: 3px 6px; font-size: 10px;" title="Tiklash">♻️</button>
                                                </form>
                                                <form action="/account-details" method="get" target="_blank" style="margin:0;">
                                                    <input type="hidden" name="phone" value="{ses}">
                                                    <button type="submit" class="btn-purple" style="padding: 3px 6px; font-size: 10px;" title="Kabinet">💻</button>
                                                </form>
                                            </div>
                                        </li>
            """
        html += """
                                    </ul>
                                </div>
                            </details>
                        </div>
        """

    html += """
                    </div>
                </details>
            </div>

            <!-- 5. ZADANIYALAR TARIXI -->
            <div class="window" id="win-history">
                <details open ontoggle="handleToggle('win-history', this)">
                    <summary class="window-header">
                        <span>📋 Zadaniyalar Tarixi</span>
                        <div class="window-controls">
                            <form action="/clear-history" method="post" style="margin:0;">
                                <button type="submit" class="btn-danger">Tozalash</button>
                            </form>
                            <button type="button" class="btn-toggle active" id="btn-win-history" onclick="event.stopPropagation(); toggleWindow('win-history')">ON</button>
                        </div>
                    </summary>
                    <div class="window-body">
                        <ul>
    """
    if task_history:
        for h in reversed(task_history):
            html += f"""
                            <li>
                                <div style="font-size: 11px;">
                                    <b>🕒</b> {h['time']} | <b>🎯</b> {h['target']} | <b>{h['type'].upper()}</b>
                                </div>
                                <div>
                                    <span class="badge badge-green">M: {h['success']}</span>
                                    <span class="badge badge-red">X: {h['failed']}</span>
                                </div>
                            </li>
            """
    else:
        html += "<p style='color: #94a3b8; text-align: center; margin: 4px 0; font-size: 11px;'>Tarix bo'sh.</p>"

    html += """
                        </ul>
                    </div>
                </details>
            </div>

            <script>
                let taskCounter = 0;

                function setTaskType(index, type, btnEl) {
                    let parent = document.getElementById('task-item-' + index);
                    parent.querySelectorAll('.task-tab').forEach(t => t.classList.remove('active'));
                    btnEl.classList.add('active');
                    document.getElementById('task_type_' + index).value = type;

                    let extraCont = document.getElementById('extra_container_' + index);
                    let reactCont = document.getElementById('reaction_container_' + index);
                    let targetField = document.getElementById('target_' + index);

                    if (type === 'join' || type === 'view') {
                        extraCont.style.display = 'none';
                        reactCont.style.display = 'none';
                        targetField.placeholder = "Kanal yoki post ssilkasi (https://t.me/...)";
                    } else if (type === 'msg') {
                        extraCont.style.display = 'block';
                        reactCont.style.display = 'none';
                        document.getElementById('msg_' + index).placeholder = "Yuboriladigan xabar matni...";
                    } else if (type === 'bot') {
                        extraCont.style.display = 'block';
                        reactCont.style.display = 'none';
                        document.getElementById('msg_' + index).placeholder = "Botga buyruq (masalan: /start)...";
                    } else if (type === 'react') {
                        extraCont.style.display = 'none';
                        reactCont.style.display = 'block';
                        targetField.placeholder = "Post ssilkasi (Masalan: https://t.me/kanal/123)";
                    }
                }

                async function scanReactions(index) {
                    let target = document.getElementById('target_' + index).value;
                    if (!target) {
                        alert("Avval post ssilkasini kiriting!");
                        return;
                    }
                    let btnContainer = document.getElementById('reaction_buttons_' + index);
                    btnContainer.innerHTML = "<span style='color:#38bdf8; font-size:11px;'>Skanerlanmoqda...</span>";
                    
                    try {
                        let res = await fetch('/api/scan-reactions?target=' + encodeURIComponent(target));
                        let data = await res.json();
                        btnContainer.innerHTML = "";
                        
                        let emojis = (data.reactions && data.reactions.length > 0) ? data.reactions : [{"type": "emoji", "val": "🔥"}];

                        let autoBtn = document.createElement('button');
                        autoBtn.type = "button";
                        autoBtn.style = "padding:6px 14px; background:#16a34a; border:1px solid #38bdf8; border-radius:6px; cursor:pointer; color:#fff; font-size:12px; font-weight:bold; width:100%; margin-bottom:6px;";
                        autoBtn.innerText = "✨ Avtomatik Har Xil (Tavsiya etiladi)";
                        autoBtn.onclick = () => {
                            document.getElementById('reaction_input_' + index).value = "auto";
                            btnContainer.querySelectorAll('button').forEach(btn => btn.style.background = "#1e293b");
                            autoBtn.style.background = "#16a34a";
                        };
                        btnContainer.appendChild(autoBtn);

                        emojis.forEach((item, i) => {
                            let b = document.createElement('button');
                            b.type = "button";
                            b.style = "padding:6px 12px; background:#1e293b; border:1px solid #38bdf8; border-radius:6px; cursor:pointer; color:#fff; font-size:12px; font-weight:bold;";
                            b.innerText = (i + 1) + "-emotsiya: " + (item.type === 'custom' ? 'Maxsus' : item.val);
                            b.onclick = () => {
                                document.getElementById('reaction_input_' + index).value = item.type + ":" + item.val;
                                btnContainer.querySelectorAll('button').forEach(btn => btn.style.background = "#1e293b");
                                b.style.background = "#2563eb";
                            };
                            btnContainer.appendChild(b);
                        });
                        alert(emojis.length + " ta emotsiya topildi!");
                    } catch (e) {
                        btnContainer.innerHTML = "<span style='color:#f87171; font-size:11px;'>Tarmoq xatoligi!</span>";
                    }
                }

                function addTaskRow() {
                    let totalTasks = document.querySelectorAll('.task-row').length;
                    if (totalTasks >= 5) {
                        alert("Maksimal 5 ta zadaniya qo'shish mumkin!");
                        return;
                    }
                    taskCounter++;
                    let idx = taskCounter;
                    let container = document.getElementById('tasks-container');
                    let div = document.createElement('div');
                    div.className = 'task-row';
                    div.id = 'task-item-' + idx;
                    div.innerHTML = `
                        <b style="color: #38bdf8; font-size: 12px;">Zadaniya:</b>
                        <button type="button" class="remove-task" onclick="document.getElementById('task-item-${idx}').remove();">✖</button>
                        <div class="task-tabs" style="margin-top: 6px;">
                            <button type="button" class="task-tab active" onclick="setTaskType(${idx}, 'join', this)">📢 Obuna</button>
                            <button type="button" class="task-tab" onclick="setTaskType(${idx}, 'view', this)">👁️ Prosmotr</button>
                            <button type="button" class="task-tab" onclick="setTaskType(${idx}, 'msg', this)">💬 Xabar</button>
                            <button type="button" class="task-tab" onclick="setTaskType(${idx}, 'bot', this)">🤖 Bot</button>
                            <button type="button" class="task-tab" onclick="setTaskType(${idx}, 'react', this)">🔥 Emotsiya</button>
                        </div>
                        <input type="hidden" name="task_types" id="task_type_${idx}" value="join">
                        <input type="text" name="targets" id="target_${idx}" placeholder="Kanal yoki post ssilkasi..." required style="margin-top: 4px;">
                        
                        <div id="extra_container_${idx}" style="display:none; margin-top:4px;">
                            <input type="text" name="messages" id="msg_${idx}" placeholder="Xabar matni yoki buyruq...">
                        </div>
                        <div id="reaction_container_${idx}" style="display:none; margin-top:6px;">
                            <button type="button" class="btn-purple" onclick="scanReactions(${idx})" style="font-size:11px; padding:6px 12px;">🔍 Emotsiyalarni Skaner Qilish</button>
                            <div id="reaction_buttons_${idx}" style="display:flex; gap:6px; margin-top:6px; flex-wrap:wrap;"></div>
                            <input type="hidden" name="reactions" id="reaction_input_${idx}" value="auto">
                        </div>
                    `;
                    container.appendChild(div);
                }

                function toggleWindow(winId) {
                    let win = document.getElementById(winId).querySelector('details');
                    win.open = !win.open;
                }

                function handleToggle(winId, detailsEl) {
                    let btn = document.getElementById('btn-' + winId);
                    if (detailsEl.open) {
                        btn.innerText = 'ON';
                        btn.classList.add('active');
                    } else {
                        btn.innerText = 'OFF';
                        btn.classList.remove('active');
                    }
                }

                function filterAccounts() {
                    let input = document.getElementById('searchInput').value.toLowerCase();
                    document.querySelectorAll('.acc-item').forEach(li => {
                        li.style.display = li.getAttribute('data-text').toLowerCase().includes(input) ? "" : "none";
                    });
                }

                async function updateStats() {
                    try {
                        let res = await fetch('/api/stats');
                        let data = await res.json();
                        document.getElementById('ram-indicator').innerText = "RAM: " + data.app_ram + " MB";
                        document.getElementById('ext-ip').innerText = data.external_ip;
                        document.getElementById('loc-ip').innerText = data.local_ip;
                    } catch (e) {}
                }

                async function checkProgress() {
                    try {
                        let res = await fetch('/api/progress');
                        let data = await res.json();
                        let box = document.getElementById('live-progress-box');
                        if (data.is_running) {
                            box.style.display = 'block';
                            document.getElementById('prog-bar').style.width = data.percent + '%';
                            document.getElementById('prog-title').innerText = "⏳ " + data.info;
                            document.getElementById('prog-time').innerText = data.elapsed + "s";
                            document.getElementById('prog-counts').innerText = data.current + " / " + data.total + " (" + data.percent + "%)";
                            document.getElementById('prog-status').innerHTML = "M: <b style='color:#4ade80;'>" + data.success + "</b> | X: <b style='color:#f87171;'>" + data.failed + "</b>";
                        } else {
                            if (box.style.display === 'block') { window.location.reload(); }
                        }
                    } catch (e) {}
                }

                async function startAction(event, url) {
                    event.preventDefault();
                    let res = await fetch(url, { method: 'POST', body: new FormData(event.target) });
                    let json = await res.json();
                    if (json.error) { alert(json.error); }
                    else { document.getElementById('live-progress-box').style.display = 'block'; }
                }

                setInterval(updateStats, 3000);
                setInterval(checkProgress, 1000);
                updateStats();
            </script>
        </body>
    </html>
    """
    return html

@app.post("/backup-sessions")
async def backup_sessions():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for f in os.listdir(SESSION_DIR):
        if f.endswith('.session'):
            try:
                shutil.copy(os.path.join(SESSION_DIR, f), os.path.join(BACKUP_DIR, f))
            except Exception:
                pass
    return RedirectResponse("http://127.0.0.1:8000/?msg=Sessiyalar+zaxiralandi!", status_code=303)

@app.get("/download-backup-zip")
async def download_backup_zip():
    zip_path = "/home/kaliaza/telegram_panel_pc/sessions_backup"
    shutil.make_archive(zip_path, 'zip', SESSION_DIR)
    return FileResponse(f"{zip_path}.zip", media_type="application/x-zip-compressed", filename="telegram_sessions_backup.zip")

@app.post("/upload-session")
async def upload_session(session_file: UploadFile = File(...)):
    if not session_file.filename.endswith('.session'):
        return RedirectResponse("http://127.0.0.1:8000/?msg=Xatolik:+Faqat+.session+fayli!", status_code=303)
    
    os.makedirs(SESSION_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    file_path = os.path.join(SESSION_DIR, session_file.filename)
    backup_path = os.path.join(BACKUP_DIR, session_file.filename)
    
    try:
        content = await session_file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        with open(backup_path, "wb") as buffer:
            buffer.write(content)
        return RedirectResponse(f"http://127.0.0.1:8000/?msg={session_file.filename}+yuklandi!", status_code=303)
    except Exception as e:
        return RedirectResponse(f"http://127.0.0.1:8000/?msg=Xatolik:+{e}", status_code=303)

@app.post("/restore-sessions")
async def restore_sessions():
    os.makedirs(SESSION_DIR, exist_ok=True)
    restored_count = 0
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.endswith('.session'):
                try:
                    shutil.copy(os.path.join(BACKUP_DIR, f), os.path.join(SESSION_DIR, f))
                    restored_count += 1
                except Exception:
                    pass
    return RedirectResponse(f"http://127.0.0.1:8000/?msg={restored_count}+ta+akkaunt+tiklandi!", status_code=303)

@app.post("/restore-single")
async def restore_single(phone: str = Form(...)):
    clean_phone = phone.replace('+', '').strip()
    backup_file = f"{clean_phone}.session"
    src = os.path.join(BACKUP_DIR, backup_file)
    dst = os.path.join(SESSION_DIR, backup_file)
    
    if os.path.exists(src):
        try:
            os.makedirs(SESSION_DIR, exist_ok=True)
            shutil.copy(src, dst)
            return RedirectResponse(f"http://127.0.0.1:8000/?msg={clean_phone}+tiklandi!", status_code=303)
        except Exception:
            pass
    return RedirectResponse("http://127.0.0.1:8000/?msg=Xatolik:+Topilmadi!", status_code=303)

@app.post("/check-accounts-fast")
async def check_accounts_fast():
    if task_state["is_running"]:
        return JSONResponse({"error": "Band!"})

    all_files = [f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session') and f.replace('.session', '').replace('+', '').isdigit()]
    
    task_state["is_running"] = True
    task_state["total"] = len(all_files)
    task_state["current"] = 0
    task_state["success"] = 0
    task_state["failed"] = 0
    task_state["start_time"] = time.time()
    task_state["info"] = "Tezkor tekshirilmoqda..."

    async def check_one(ses_name):
        session_path = os.path.join(SESSION_DIR, ses_name)
        client = TelegramClient(session_path, api_id, api_hash, request_retries=2, connection_retries=2)
        try:
            await client.connect()
            if await client.is_user_authorized():
                account_cache[ses_name] = {"status": "Faol", "cls": "badge-green"}
                task_state["success"] += 1
            else:
                account_cache[ses_name] = {"status": "Yaroqsiz", "cls": "badge-red"}
                task_state["failed"] += 1
            await client.disconnect()
        except:
            account_cache[ses_name] = {"status": "Xato", "cls": "badge-red"}
            task_state["failed"] += 1
        task_state["current"] += 1

    async def run_fast_checking():
        await asyncio.gather(*(check_one(ses) for ses in all_files))
        task_state["is_running"] = False

    asyncio.create_task(run_fast_checking())
    return JSONResponse({"status": "started"})

@app.post("/check-accounts")
async def check_accounts():
    if task_state["is_running"]:
        return JSONResponse({"error": "Band!"})

    all_files = [f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session') and f.replace('.session', '').replace('+', '').isdigit()]
    
    task_state["is_running"] = True
    task_state["total"] = len(all_files)
    task_state["current"] = 0
    task_state["success"] = 0
    task_state["failed"] = 0
    task_state["start_time"] = time.time()
    task_state["info"] = "To'liq tekshirilmoqda..."

    now = datetime.now(timezone.utc)
    async def check_one_full(ses_name):
        session_path = os.path.join(SESSION_DIR, ses_name)
        client = TelegramClient(session_path, api_id, api_hash, request_retries=2, connection_retries=2)
        try:
            await client.connect()
            if await client.is_user_authorized():
                sms_text = "Faol"
                try:
                    async for msg in client.iter_messages(777000, limit=1):
                        if msg.date:
                            diff = (now - msg.date).total_seconds() / 3600
                            sms_text = f"{round(diff)}h SMS"
                except:
                    pass
                account_cache[ses_name] = {"status": sms_text, "cls": "badge-green"}
                task_state["success"] += 1
            else:
                account_cache[ses_name] = {"status": "Yaroqsiz", "cls": "badge-red"}
                task_state["failed"] += 1
            await client.disconnect()
        except:
            account_cache[ses_name] = {"status": "Xato", "cls": "badge-red"}
            task_state["failed"] += 1
        task_state["current"] += 1

    async def run_checking():
        await asyncio.gather(*(check_one_full(ses) for ses in all_files))
        task_state["is_running"] = False

    asyncio.create_task(run_checking())
    return JSONResponse({"status": "started"})

@app.post("/broadcast")
async def broadcast(task_types: List[str] = Form(...), targets: List[str] = Form(...), messages: List[str] = Form([]), reactions: List[str] = Form([]), mode: str = Form("pro"), selected_groups: List[str] = Form([])):
    if task_state["is_running"]:
        return JSONResponse({"error": "Vazifa bajarilmoqda!"})
    if not selected_groups:
        return JSONResponse({"error": "Guruh tanlanmadi!"})

    tasks_to_run = []
    for i in range(len(targets)):
        if targets[i].strip():
            t_type = task_types[i] if i < len(task_types) else "join"
            t_target = targets[i].strip()
            t_msg = messages[i].strip() if i < len(messages) and messages[i] else ""
            t_react = reactions[i] if i < len(reactions) and reactions[i] else "auto"
            tasks_to_run.append({"type": t_type, "target": t_target, "msg": t_msg, "reaction": t_react})

    if not tasks_to_run:
        return JSONResponse({"error": "Hech qanday zadaniya kiritilmadi!"})

    all_files = sorted([f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session') and f.replace('.session', '').replace('+', '').isdigit()])
    target_accounts = [ses for i, ses in enumerate(all_files) if str((i // 10) + 1) in selected_groups]

    task_state["is_running"] = True
    task_state["total"] = len(target_accounts) * len(tasks_to_run)
    task_state["current"] = 0
    task_state["success"] = 0
    task_state["failed"] = 0
    task_state["start_time"] = time.time()
    task_state["info"] = f"Aniq va xavfsiz bajarilmoqda ({len(tasks_to_run)} ta zadaniya)..."

    async def run_task():
        for ses_name in target_accounts:
            session_path = os.path.join(SESSION_DIR, ses_name)
            client = TelegramClient(session_path, api_id, api_hash, request_retries=3, connection_retries=3, timeout=10)
            connected = False
            try:
                await asyncio.wait_for(client.connect(), timeout=8.0)
                if await client.is_user_authorized():
                    connected = True
            except:
                pass

            if not connected:
                task_state["current"] += len(tasks_to_run)
                task_state["failed"] += len(tasks_to_run)
                try:
                    await client.disconnect()
                except:
                    pass
                continue

            for task in tasks_to_run:
                success_flag = False
                for attempt in range(2): # Xato bo'lsa 1 marta qayta urinish
                    try:
                        entity_raw = task["target"]
                        msg_id = None
                        
                        if entity_raw.startswith("https://t.me/"):
                            if "/c/" in entity_raw:
                                parts = entity_raw.split("/")
                                channel_id = int("-100" + parts[parts.index("c") + 1])
                                msg_id = int(parts[-1])
                                entity = await client.get_entity(channel_id)
                            else:
                                clean_link = entity_raw.split("https://t.me/")[-1].strip("/")
                                if "/" in clean_link:
                                    parts = clean_link.split("/")
                                    entity = await client.get_entity("@" + parts[0])
                                    try:
                                        msg_id = int(parts[1])
                                    except:
                                        pass
                                else:
                                    entity = await client.get_entity("@" + clean_link)
                        else:
                            entity = await client.get_entity(entity_raw)

                        # 1. OBUNA
                        if task["type"] == "join":
                            try:
                                await client(JoinChannelRequest(entity))
                                success_flag = True
                                break
                            except Exception as e:
                                if "CHANNELS_TOO_MUCH" in str(e) or "USER_ALREADY_PARTICIPANT" in str(e):
                                    success_flag = True
                                    break
                                raise e

                        # 2. PROSMOTR
                        elif task["type"] == "view":
                            target_msg_ids = []
                            if msg_id:
                                target_msg_ids.append(msg_id)
                            else:
                                async for m in client.iter_messages(entity, limit=3):
                                    target_msg_ids.append(m.id)
                            
                            if target_msg_ids:
                                await client(GetMessagesViewsRequest(
                                    peer=entity,
                                    id=target_msg_ids,
                                    increment=True
                                ))
                                success_flag = True
                                break

                        # 3. XABAR YUBORISH
                        elif task["type"] == "msg":
                            await client.send_message(entity, randomize_message(task["msg"]))
                            success_flag = True
                            break

                        # 4. BOT
                        elif task["type"] == "bot":
                            cmd = task["msg"] if task["msg"] else "/start"
                            await client.send_message(entity, cmd)
                            await asyncio.sleep(0.5)
                            try:
                                async for msg in client.iter_messages(entity, limit=2):
                                    if msg.reply_markup and hasattr(msg.reply_markup, 'rows'):
                                        for row in msg.reply_markup.rows:
                                            for button in row.buttons:
                                                btn_text = getattr(button, 'text', '').lower()
                                                if any(w in btn_text for w in ['start', 'boshlash', 'play', 'obuna', 'подписаться', 'verify', 'joined']):
                                                    await button.click()
                            except:
                                pass
                            success_flag = True
                            break

                        # 5. REACTION (Aniq va xilma-xil)
                        elif task["type"] == "react":
                            try:
                                await client(JoinChannelRequest(entity))
                            except:
                                pass

                            target_msg_id = msg_id
                            if not target_msg_id:
                                async for m in client.iter_messages(entity, limit=1):
                                    target_msg_id = m.id
                                    break
                            
                            if target_msg_id:
                                msg_obj = await client.get_messages(entity, ids=target_msg_id)
                                available_reactions = []

                                if msg_obj and msg_obj.reactions and msg_obj.reactions.results:
                                    for r in msg_obj.reactions.results:
                                        if isinstance(r.reaction, ReactionEmoji):
                                            available_reactions.append(ReactionEmoji(emoticon=r.reaction.emoticon))
                                        elif isinstance(r.reaction, ReactionCustomEmoji):
                                            available_reactions.append(ReactionCustomEmoji(document_id=r.reaction.document_id))

                                if not available_reactions:
                                    default_emojis = ["🔥", "👍", "❤️", "👏", "😁", "🎉", "⚡", "🏆", "🎯", "⭐"]
                                    chosen_emo = random.choice(default_emojis)
                                    available_reactions = [ReactionEmoji(emoticon=chosen_emo)]

                                r_input = task["reaction"]
                                reaction_payload = None
                                if r_input != "auto" and ":" in r_input:
                                    r_type, r_val = r_input.split(":", 1)
                                    if r_type == "custom" and r_val.isdigit():
                                        reaction_payload = ReactionCustomEmoji(document_id=int(r_val))
                                    else:
                                        reaction_payload = ReactionEmoji(emoticon=r_val)
                                else:
                                    reaction_payload = random.choice(available_reactions)

                                await client(SendReactionRequest(
                                    peer=entity,
                                    msg_id=target_msg_id,
                                    reaction=[reaction_payload]
                                ))
                                success_flag = True
                                break
                    except errors.FloodWaitError as fw:
                        await asyncio.sleep(min(fw.seconds, 5))
                    except Exception:
                        await asyncio.sleep(0.5)

                if success_flag:
                    task_state["success"] += 1
                else:
                    task_state["failed"] += 1
                
                task_state["current"] += 1

            try:
                await client.disconnect()
            except:
                pass
            
            # Xatoliklarni oldini olish uchun Pro rejimgacha biroz barqaror pauza
            if mode == "fast":
                await asyncio.sleep(0.3)
            else:
                await asyncio.sleep(random.uniform(0.8, 1.5))

        task_state["is_running"] = False
        task_history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": f"{len(tasks_to_run)} ta turli zadaniya",
            "type": "multi-task",
            "success": task_state["success"],
            "failed": task_state["failed"]
        })

    asyncio.create_task(run_task())
    return JSONResponse({"status": "started"})

@app.post("/clear-history")
async def clear_history():
    task_history.clear()
    return RedirectResponse("http://127.0.0.1:8000/", status_code=303)

@app.get("/account-details", response_class=HTMLResponse)
async def account_details(phone: str, chat_id: int = None, q: str = ""):
    clean_phone = phone.replace('+', '').strip()
    session_file = ""
    for f in os.listdir(SESSION_DIR):
        if f.endswith('.session') and clean_phone in f:
            session_file = f
            break

    if not session_file:
        return HTMLResponse("<h3>Topilmadi!</h3><a href='http://127.0.0.1:8000/'>Orqaga</a>")

    orig_path = os.path.join(SESSION_DIR, session_file)
    temp_session_name = f"temp_{clean_phone}_{int(time.time())}"
    temp_path = os.path.join(SESSION_DIR, f"{temp_session_name}.session")
    
    try:
        shutil.copy(orig_path, temp_path)
    except:
        pass

    client = TelegramClient(os.path.join(SESSION_DIR, temp_session_name), api_id, api_hash)
    dialogs = []
    messages = []
    active_title = ""
    phone_num = phone

    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            if os.path.exists(temp_path): os.remove(temp_path)
            return HTMLResponse("<h3>Yaroqsiz!</h3><a href='http://127.0.0.1:8000/'>Orqaga</a>")

        me = await client.get_me()
        phone_num = f"+{me.phone}" if me.phone else phone

        async for dialog in client.iter_dialogs(limit=25):
            title = dialog.name or ""
            if q and q.lower() not in title.lower():
                continue
            dialogs.append({"title": title, "id": dialog.id})

        if chat_id:
            try:
                entity = await client.get_entity(chat_id)
                active_title = getattr(entity, 'title', getattr(entity, 'first_name', 'Chat'))
                async for msg in client.iter_messages(entity, limit=10):
                    messages.append({
                        "text": msg.text or "[Media]", 
                        "sender": "Siz" if msg.out else "Boshqa", 
                        "date": str(msg.date)[11:19]
                    })
                messages.reverse()
            except:
                pass

        await client.disconnect()
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return HTMLResponse(f"<h3>Xatolik: {e}</h3><a href='http://127.0.0.1:8000/'>Orqaga</a>")

    if os.path.exists(temp_path):
        os.remove(temp_path)

    html = f"""
    <html>
        <head>
            <title>Kabinet: {phone}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 15px; margin: 0; }}
                .window {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 12px; }}
                .btn-back {{ padding: 6px 12px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; margin-bottom: 12px; font-size: 12px; }}
                ul {{ list-style: none; padding: 0; max-height: 350px; overflow-y: auto; }}
                li {{ background: #0f172a; margin: 4px 0; padding: 8px; border-radius: 6px; border: 1px solid #334155; font-size: 12px; }}
                .chat-box {{ background: #0f172a; padding: 10px; border-radius: 6px; height: 300px; overflow-y: auto; margin-bottom: 8px; border: 1px solid #334155; }}
                .msg {{ margin: 6px 0; padding: 8px 12px; border-radius: 6px; max-width: 85%; font-size: 12px; line-height: 1.3; }}
                .msg-out {{ background: #1e3a8a; margin-left: auto; text-align: right; border: 1px solid #3b82f6; }}
                .msg-in {{ background: #1e293b; border: 1px solid #475569; }}
                input, textarea, button {{ padding: 8px; background: #0f172a; border: 1px solid #475569; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 12px; }}
            </style>
        </head>
        <body>
            <a href="http://127.0.0.1:8000/" class="btn-back">⬅️ Panelga Qaytish</a>
            <h2>💻 Kabinet: {phone_num}</h2>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <div class="window" style="flex:1; min-width:280px;">
                    <h3>📂 Chatlar</h3>
                    <form method="get" action="/account-details">
                        <input type="hidden" name="phone" value="{phone}">
                        <input type="text" name="q" value="{q}" placeholder="🔍 Qidirish..." style="width:100%; margin-bottom:6px;">
                    </form>
                    <ul>
    """
    for d in dialogs:
        html += f"<li><a href='/account-details?phone={phone}&chat_id={d['id']}&q={q}' style='color:#38bdf8; text-decoration:none;'>{d['title']}</a></li>"
    html += f"""
                    </ul>
                </div>
                <div class="window" style="flex:1.5; min-width:320px;">
                    <h3>💬 {active_title if chat_id else "Chat tanlanmagan"}</h3>
    """
    if chat_id:
        html += '<div class="chat-box">'
        for m in messages:
            cls = "msg-out" if m["sender"] == "Siz" else "msg-in"
            html += f'<div class="msg {cls}"><b style="color:#38bdf8;">{m["sender"]}:</b> {m["text"]}<span style="font-size:9px; color:#94a3b8; display:block; margin-top:2px;">{m["date"]}</span></div>'
        html += f"""
                    </div>
                    <form action="/send-message" method="post">
                        <input type="hidden" name="phone" value="{phone}">
                        <input type="hidden" name="chat_id" value="{chat_id}">
                        <textarea name="message_text" placeholder="Xabar..." required rows="2" style="width:100%;"></textarea>
                        <button type="submit" style="background:#2563eb; margin-top:4px; width:100%;">📤 Yuborish</button>
                    </form>
        """
    else:
        html += "<p style='color:#94a3b8; text-align:center; margin-top:80px; font-size:12px;'>Chatni tanlang</p>"
    html += """
                </div>
            </div>
        </body>
    </html>
    """
    return html

@app.post("/send-message")
async def send_message(phone: str = Form(...), chat_id: int = Form(...), message_text: str = Form(...)):
    clean_phone = phone.replace('+', '').strip()
    session_path = ""
    for f in os.listdir(SESSION_DIR):
        if f.endswith('.session') and clean_phone in f:
            session_path = os.path.join(SESSION_DIR, f.replace('.session', ''))
            break

    if session_path:
        client = TelegramClient(session_path, api_id, api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await client.send_message(await client.get_entity(chat_id), message_text)
            await client.disconnect()
        except:
            pass
    return RedirectResponse(f"/account-details?phone={phone}&chat_id={chat_id}", status_code=303)
