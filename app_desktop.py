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

class TelegramDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Telegram Desktop - Account Panel")
        self.geometry("950x600")
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Chap panel (Akkauntlar ro'yxati)
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="📱 Akkauntlar & Botlar", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)
        
        self.acc_scroll = ctk.CTkScrollableFrame(self.sidebar, label_text="Barcha sessiyalar")
        self.acc_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # O'ng panel (Chatlar va xabarlar)
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(1, weight=1)
        
        self.chat_title = ctk.CTkLabel(self.chat_frame, text="Akkaunt tanlanmagan", font=ctk.CTkFont(size=16, weight="bold"))
        self.chat_title.grid(row=0, column=0, sticky="w", pady=10)
        
        self.msg_box = ctk.CTkTextbox(self.chat_frame, width=600, corner_radius=8)
        self.msg_box.grid(row=1, column=0, sticky="nsew")
        self.msg_box.insert("0.0", "Akkaunt ustiga bosing va xabarlarni o'qing...\n(Spamdan himoyalangan xavfsiz o'qish rejimi)")
        
        self.load_accounts()

    def load_accounts(self):
        sessions = sorted([f.replace('.session', '') for f in os.listdir(SESSION_DIR) if f.endswith('.session')])
        
        for ses in sessions:
            btn = ctk.CTkButton(self.acc_scroll, text=f"+{ses}", fg_color="#2b2b2b", hover_color="#3b3b3b",
                                command=lambda s=ses: threading.Thread(target=self.open_account, args=(s,)).start())
            btn.pack(fill="x", pady=5, padx=5)

    def open_account(self, ses_name):
        path = os.path.join(SESSION_DIR, f"{ses_name}.session")
        self.chat_title.configure(text=f"⏳ Ulanmoqda: +{ses_name}...")
        self.msg_box.delete("0.0", "end")
        
        async def fetch_data():
            try:
                client = TelegramClient(path, api_id, api_hash, connection_retries=2, timeout=5)
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    name = me.first_name or "Ismsiz"
                    self.chat_title.configure(text=f"👤 {name} (@{me.username if me.username else 'username yo\'q'})")
                    
                    self.msg_box.insert("end", "📥 Oxirgi chatlar va xabarlar yuklanmoqda...\n\n")
                    
                    # Xavfsiz o'qish (Spam bo'lmasligi uchun cheklov va pauza bilan)
                    async for dialog in client.iter_dialogs(limit=15):
                        self.msg_box.insert("end", f"💬 {dialog.name} — (Oxirgi xabar: {dialog.date.strftime('%Y-%m-%d %H:%M') if dialog.date else 'Noma\'lum'})\n")
                        await asyncio.sleep(0.05) # Tabiiy kechikish
                else:
                    self.chat_title.configure(text=f"❌ Sessiya yaroqsiz: +{ses_name}")
                await client.disconnect()
            except Exception as e:
                self.chat_title.configure(text=f"⚠️ Xatolik: +{ses_name}")
                self.msg_box.insert("end", f"Ulanishda xatolik yuz berdi: {str(e)}")

        asyncio.run(fetch_data())

if __name__ == "__main__":
    app = TelegramDesktopApp()
    app.mainloop()
