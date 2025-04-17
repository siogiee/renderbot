# Let's now modify the original bot.py with:
# - Jakarta timezone support
# - /hariini, /mingguini, /bulanini commands

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pytz
import os
import json

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_json = os.environ["GOOGLE_CREDENTIALS"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(credentials_json), scope)
client = gspread.authorize(creds)
sheet = client.open("Catatan Dompet").sheet1  # Ganti dengan nama sheet kamu

# Logging
logging.basicConfig(level=logging.INFO)

# Timezone Jakarta
tz = pytz.timezone("Asia/Jakarta")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirim pengeluaranmu dengan format: Keterangan, Jumlah\\nContoh: Ayam Goreng, 20000")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "," not in text:
        await update.message.reply_text("Format salah. Gunakan format: Keterangan, Jumlah")
        return

    try:
        keterangan, jumlah_str = [x.strip() for x in text.split(",", 1)]
        jumlah = int(jumlah_str)
        tanggal = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        sheet.append_row([tanggal, keterangan, jumlah])

        # Ambil total pengeluaran hari ini
        records = sheet.get_all_records()
        total = sum(
            row["Jumlah"] for row in records
            if row["Tanggal"].startswith(datetime.now(tz).strftime("%Y-%m-%d"))
        )

        jumlah_rp = f"Rp{jumlah:,}".replace(",", ".")
        total_rp = f"Rp{total:,}".replace(",", ".")

        await update.message.reply_text(f"Tercatat: {keterangan} - {jumlah_rp}\\nTotal pengeluaran: {total_rp}")
    except Exception as e:
        await update.message.reply_text("Terjadi kesalahan saat memproses data.")

async def laporan_hariini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tanggal_hariini = datetime.now(tz).strftime("%Y-%m-%d")
    records = sheet.get_all_records()
    total = sum(
        row["Jumlah"] for row in records
        if row["Tanggal"].startswith(tanggal_hariini)
    )
    total_rp = f"Rp{total:,}".replace(",", ".")
    await update.message.reply_text(f"Total pengeluaran hari ini: {total_rp}")

async def laporan_mingguini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sekarang = datetime.now(tz)
    awal_minggu = sekarang - timedelta(days=sekarang.weekday())
    records = sheet.get_all_records()
    total = 0
    for row in records:
        try:
            waktu = datetime.strptime(row["Tanggal"], "%Y-%m-%d %H:%M:%S")
            waktu = tz.localize(waktu)
            if waktu >= awal_minggu:
                total += row["Jumlah"]
        except:
            pass
    total_rp = f"Rp{total:,}".replace(",", ".")
    await update.message.reply_text(f"Total pengeluaran minggu ini: {total_rp}")

async def laporan_bulanini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sekarang = datetime.now(tz)
    bulan_ini = sekarang.strftime("%Y-%m")
    records = sheet.get_all_records()
    total = sum(
        row["Jumlah"] for row in records
        if row["Tanggal"].startswith(bulan_ini)
    )
    total_rp = f"Rp{total:,}".replace(",", ".")
    await update.message.reply_text(f"Total pengeluaran bulan ini: {total_rp}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hariini", laporan_hariini))
    app.add_handler(CommandHandler("mingguini", laporan_mingguini))
    app.add_handler(CommandHandler("bulanini", laporan_bulanini))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
