import os
import sys
import asyncio
import time
from datetime import datetime, timezone
from telethon import TelegramClient

api_id = 39286516
api_hash = '9f5cedcd688bbaade3398c8c8c30f2b8'
SESSION_DIR = "."

def clear():
    os.system('clear')

def modern_banner():
    print("\033[1;36m")
    print("  ████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗")
    print("  ╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║")
    print("     ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║")
    print("     ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║ ╚═╝ ██║")
    print("     ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║     ██║")
    print("\033[1;35m  =================== [ PC TERMINAL MANAGEMENT PANEL ] ===================\033[0m")

def make_progress_bar(current, total, length=20):
    percent = float(current) / total
    filled = int(round(length * percent))
    bar = '█' * filled + '░' * (length - filled)
    return f"\033[1;32m[{bar}] {int(percent * 100)}% ({current}/{total})\033[0m"

async def pc_list():
    all_files = sorted([f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session')])
    if not all_files:
        print("\033[1;31m❌ Sessiya topilmadi!\033[0m")
        return
    
    total = len(all_files)
    print(f"\n\033[1;33m⏳ Akkaunt ma'lumotlari yuklanmoqda ({total} ta)...\033[0m")
    
    for idx, ses in enumerate(all_files, 1):
        path = os.path.join(SESSION_DIR, f"{ses}.session")
        name = "Noma'lum"
        user_id = "-"
        username = "Username yo'q"
        try:
            client = TelegramClient(path, api_id, api_hash, connection_retries=2, timeout=5)
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                if me:
                    name = me.first_name or "Ismsiz"
                    user_id = str(me.id)
                    username = f"@{me.username}" if me.username else "Username yo'q"
            await client.disconnect()
        except:
            name = "Ulanmadi"
        
        print(f" \033[1;36m[📱 +{ses}]\033[0m 👤 {name} | ID: {user_id} | {username}")
        sys.stdout.write(f"\r{make_progress_bar(idx, total)}")
        sys.stdout.flush()
        await asyncio.sleep(0.1)
    print("\n")

async def pc_check():
    all_files = [f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    if not all_files:
        print("\033[1;31m❌ Sessiya topilmadi!\033[0m")
        return

    total = len(all_files)
    success, failed = 0, 0
    print(f"\n\033[1;33m⏳ Tezkor tekshiruv boshlandi ({total} ta)...\033[0m")

    for idx, ses in enumerate(all_files, 1):
        path = os.path.join(SESSION_DIR, f"{ses}.session")
        try:
            client = TelegramClient(path, api_id, api_hash, connection_retries=2, timeout=5)
            await client.connect()
            if await client.is_user_authorized():
                success += 1
            else:
                failed += 1
            await client.disconnect()
        except:
            failed += 1
        
        sys.stdout.write(f"\r{make_progress_bar(idx, total)} | 🟢: {success} | 🔴: {failed}")
        sys.stdout.flush()
        await asyncio.sleep(0.1)

    print(f"\n\n\033[1;32m✅ Tekshiruv yakunlandi! Faol: {success} | Yaroqsiz: {failed}\033[0m\n")

async def pc_sms():
    all_files = [f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    if not all_files:
        print("\033[1;31m❌ Sessiya topilmadi!\033[0m")
        return

    total = len(all_files)
    now = datetime.now(timezone.utc)
    print(f"\n\033[1;33m⚡ SMS vaqtlari tekshirilmoqda ({total} ta)...\033[0m")

    for idx, ses in enumerate(all_files, 1):
        path = os.path.join(SESSION_DIR, f"{ses}.session")
        sms_info = "SMS yo'q"
        try:
            client = TelegramClient(path, api_id, api_hash, connection_retries=2, timeout=5)
            await client.connect()
            if await client.is_user_authorized():
                async for msg in client.iter_messages(777000, limit=1):
                    if msg.date:
                        diff = (now - msg.date).total_seconds() / 3600
                        if diff <= 2:
                            sms_info = f"🔴 {round(diff, 1)}s oldin"
                        elif diff <= 24:
                            sms_info = f"🟡 {round(diff)}s oldin"
                        else:
                            sms_info = f"🟢 {round(diff/24)} kun oldin"
            await client.disconnect()
        except:
            sms_info = "Xatolik"
        
        print(f" 📱 +{ses} — {sms_info}")
        sys.stdout.write(f"\r{make_progress_bar(idx, total)}")
        sys.stdout.flush()
        await asyncio.sleep(0.1)
    print("\n")

def main():
    while True:
        clear()
        modern_banner()
        
        acc_count = len([f for f in os.listdir(SESSION_DIR) if f.endswith('.session')])
        
        print(f"\033[1;32m [*] Faol Akkauntlar: \033[1;33m{acc_count} ta\033[0m")
        print("\033[1;34m─────────────────────────────────────────────────────────────────────\033[0m")
        print(" \033[1;36m[1]\033[0m 📋 Akkauntlar Ro'yxatini Ko'rish (Ism, ID, Username)")
        print(" \033[1;36m[2]\033[0m 🔄 Holatni Tekshirish (Foizli)")
        print(" \033[1;36m[3]\033[0m ⚡ SMS Vaqtlarini Tekshirish")
        print(" \033[1;31m[0]\033[0m 🚪 Chiqish")
        print("\033[1;34m─────────────────────────────────────────────────────────────────────\033[0m")
        
        choice = input("\033[1;33mKerakli raqamni tanlang (0-3): \033[0m").strip()
        
        if choice == '1':
            clear()
            asyncio.run(pc_list())
            input("\n\033[1;33mDavom etish uchun Enter bosing...\033[0m")
        elif choice == '2':
            clear()
            asyncio.run(pc_check())
            input("\n\033[1;33mDavom etish uchun Enter bosing...\033[0m")
        elif choice == '3':
            clear()
            asyncio.run(pc_sms())
            input("\n\033[1;33mDavom etish uchun Enter bosing...\033[0m")
        elif choice == '0':
            clear()
            print("\033[1;31mXayr! Panel yopildi. 👋\033[0m")
            break
        else:
            print("\033[1;31mXato raqam! Qaytadan urinib ko'ring.\033[0m")
            time.sleep(1)

if __name__ == '__main__':
    main()
