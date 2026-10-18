import os
import asyncio
import threading
import customtkinter as ctk
from telethon import TelegramClient

api_id = 39286516
api_hash = '9f5cedcd688bbaade3398c8c8c30f2b8'
SESSION_DIR = "."

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TelegramDesktopClone(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Telegram Desktop - Multi-Account Panel (39 Accounts)")
        self.geometry("1150x700")
        
        # Grid layout (3 ta ustun: 0-Akkauntlar, 1-Chatlar, 2-Xabarlar)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        # 1-Ustun: Akkauntlar paneli
        self.acc_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1f1f1f")
        self.acc_frame.grid(row=0, column=0, sticky="nsew")
        self.acc_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.acc_frame, text="🛡 Akkauntlar & Botlar (39)", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, pady=15)
        
        self.acc_scroll = ctk.CTkScrollableFrame(self.acc_frame, fg_color="transparent")
        self.acc_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # 2-Ustun: Chatlar ro'yxati
        self.chats_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#181818")
        self.chats_frame.grid(row=0, column=1, sticky="nsew")
        self.chats_frame.grid_rowconfigure(1, weight=1)
        
        self.chat_header = ctk.CTkLabel(self.chats_frame, text="Suhbatlar va Kanallar", font=ctk.CTkFont(size=15, weight="bold"))
        self.chat_header.grid(row=0, column=0, pady=15)
        
        self.chats_scroll = ctk.CTkScrollableFrame(self.chats_frame, fg_color="transparent")
        self.chats_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # 3-Ustun: Xabarlar oynasi
        self.msg_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0e0e0e")
        self.msg_frame.grid(row=0, column=2, sticky="nsew")
        self.msg_frame.grid_columnconfigure(0, weight=1)
        self.msg_frame.grid_rowconfigure(1, weight=1)
        
        self.msg_title = ctk.CTkLabel(self.msg_frame, text="Xabarlarni o'qish oynasi", font=ctk.CTkFont(size=14, weight="bold"))
        self.msg_title.grid(row=0, column=0, pady=15, sticky="w", padx=15)
        
        self.msg_box = ctk.CTkTextbox(self.msg_frame, corner_radius=6, fg_color="#171717", text_color="#ffffff")
        self.msg_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.msg_box.insert("0.0", "Chapdan xohlagan akkauntni tanlang va chat ustiga bosing...\n(Spamdan himoyalangan xavfsiz o'qish rejimi)")

        self.load_accounts()

    def load_accounts(self):
        sessions = sorted([f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session')])
        for ses in sessions:
            btn = ctk.CTkButton(self.acc_scroll, text=f"+{ses}", fg_color="#2b2b2b", hover_color="#3b3b3b",
                                command=lambda s=ses: threading.Thread(target=self.select_account, args=(s,)).start())
            btn.pack(fill="x", pady=4, padx=2)

    def select_account(self, ses_name):
        path = os.path.join(SESSION_DIR, f"{ses_name}.session")
        self.msg_title.configure(text=f"⏳ Ulanmoqda: +{ses_name}...")
        
        for widget in self.chats_scroll.winfo_children():
            widget.destroy()

        async def load_chats():
            try:
                client = TelegramClient(path, api_id, api_hash, connection_retries=2, timeout=5)
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    self.msg_title.configure(text=f"👤 {me.first_name} (@{me.username if me.username else 'id: ' + str(me.id)})")
                    
                    async for dialog in client.iter_dialogs(limit=30):
                        d_name = dialog.name or "Noma'lum"
                        btn = ctk.CTkButton(self.chats_scroll, text=d_name, fg_color="#222222", hover_color="#333333", anchor="w",
                                            command=lambda d=dialog, c=client: threading.Thread(target=self.load_messages, args=(c, d)).start())
                        btn.pack(fill="x", pady=3, padx=2)
                        await asyncio.sleep(0.01)
                else:
                    self.msg_title.configure(text=f"❌ Akkaunt yaroqsiz: +{ses_name}")
                await client.disconnect()
            except Exception as e:
                self.msg_title.configure(text=f"⚠️ Ulanishda xatolik yuz berdi")

        asyncio.run(load_chats())

    def load_messages(self, client, dialog):
        self.msg_box.delete("0.0", "end")
        self.msg_box.insert("end", f"💬 {dialog.name} yozishmalari yuklanmoqda...\n\n")

        async def fetch_msgs():
            try:
                async for message in client.iter_messages(dialog.entity, limit=25):
                    sender = "Siz" if message.out else dialog.name
                    date_str = message.date.strftime('%Y-%m-%d %H:%M') if message.date else ""
                    text = message.text or "[Media/Stiker]"
                    self.msg_box.insert("end", f"[{date_str}] {sender}: {text}\n\n")
                    await asyncio.sleep(0.01)
            except Exception as e:
                self.msg_box.insert("end", f"Xatolik: {str(e)}")

        asyncio.run(fetch_msgs())

if __name__ == "__main__":
    app = TelegramDesktopClone()
    app.mainloop()
