#!/bin/bash
echo "🚀 Telegram Panel va 2-Oyna ishga tushirilmoqda..."
/home/kaliaza/myenv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 &
/home/kaliaza/myenv/bin/uvicorn add_account:app --host 127.0.0.1 --port 8001 &
wait
