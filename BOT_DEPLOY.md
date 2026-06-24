# YouthGuard bot — serverga qo'yish

DRF allaqachon `https://sam-auth.uz` da ishlab turishi kerak (avval DRF ni deploy qiling).
Bot YouthGuard uchun bazaga muhtoj emas — faqat sam-auth.uz ga ulanadi.

## 1. Bot fayllarini serverga ko'chiring
```bash
# masalan /root/Bobur_aka_2 ga
cd /root/Bobur_aka_2
```

## 2. Virtual muhit va paketlar
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. .env tekshiruvi
`.env` ichida quyidagi turishi shart (allaqachon sozlangan):
```
YOUTHGUARD_API_URL=https://sam-auth.uz
YOUTHGUARD_BOT_SECRET=youthguard-bot-secret-2024
BOT_TOKEN=...
```

## 4. Sinab ko'rish
```bash
python app.py
```
"Bot ishga tushdi!" chiqsa — ishladi. Ctrl+C bilan to'xtating.

## 5. systemd bilan 24/7 ishlatish
```bash
# service faylini ko'chiring
sudo cp youthguard-bot.service /etc/systemd/system/
# ichidagi WorkingDirectory va ExecStart yo'llarini tekshiring!

sudo systemctl daemon-reload
sudo systemctl enable youthguard-bot
sudo systemctl start youthguard-bot
sudo systemctl status youthguard-bot
```

Loglarni kuzatish:
```bash
sudo journalctl -u youthguard-bot -f
```

## DIQQAT — bitta nusxa qoidasi
Telegram bot **faqat bitta joyda** ishlashi mumkin. Server'da ishga tushirsangiz,
kompyuteringizdagi `python app.py` ni **to'xtating** — aks holda
"Terminated by other getUpdates" xatosi chiqadi.
