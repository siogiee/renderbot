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

gc = gspread.authorize(creds)
sheet = gc.open_by_key(os.environ["SHEET_ID"]).worksheet(os.environ["WORKSHEET_NAME"])

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Timezone
tz = pytz.timezone("Asia/Jakarta")

# Hitung saldo sekarang
def get_balance():
    records = sheet.get_all_records()
    income = sum(row["Jumlah"] for row in records if row.get("Tipe", "").lower() == "pemasukan")
    spending = sum(row["Jumlah"] for row in records if row.get("Tipe", "").lower() == "pengeluaran")
    return income - spending

# Hitung pemasukan & pengeluaran dari tanggal tertentu
def get_summary(start_date):
    records = sheet.get_all_records()
    income = spending = 0
    for row in records:
        try:
            row_date = datetime.strptime(row["Tanggal"], "%Y-%m-%d %H:%M:%S").date()
            if row_date >= start_date:
                if row["Tipe"].lower() == "pemasukan":
                    income += row["Jumlah"]
                elif row["Tipe"].lower() == "pengeluaran":
                    spending += row["Jumlah"]
        except:
            continue
    return income, spending

# Handler pesan utama
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    now = datetime.now(tz)
    tanggal = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
        if ";" in text:
            # Pemasukan
            nama, jumlah = text.split(";")
            tipe = "Pemasukan"
        elif "," in text:
            # Pengeluaran
            nama, jumlah = text.split(",")
            tipe = "Pengeluaran"
        else:
            await update.message.reply_text("Format tidak dikenali. Gunakan ',' untuk pengeluaran dan ';' untuk pemasukan.")
            return

        nama = nama.strip()
        jumlah = int(jumlah.strip())

        sheet.append_row([tanggal, nama, jumlah, tipe])
        saldo = get_balance()

        response = f"✅ {tipe} sebesar Rp{jumlah:,.0f} dicatat sebagai *{nama}*.\n💰 Saldo saat ini: Rp{saldo:,.0f}"
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {e}")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirim pesan seperti:\n"
        "- `Ayam Geprek, 20000` untuk pengeluaran\n"
        "- `Gajian; 12000000` untuk pemasukan\n\n"
        "Perintah lain:\n"
        "/saldo - Cek saldo\n"
        "/harian - Ringkasan hari ini\n"
        "/mingguan - Ringkasan minggu ini\n"
        "/bulanan - Ringkasan bulan ini",
        parse_mode="Markdown"
    )

# Perintah tambahan
async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saldo = get_balance()
    await update.message.reply_text(f"💰 Saldo saat ini: Rp{saldo:,.0f}")

async def summary_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(tz).date()
    income, spending = get_summary(today)
    await update.message.reply_text(
        f"📅 Ringkasan Hari Ini:\n📥 Pemasukan: Rp{income:,.0f}\n📤 Pengeluaran: Rp{spending:,.0f}"
    )

async def summary_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(tz).date()
    start_of_week = today - timedelta(days=today.weekday())
    income, spending = get_summary(start_of_week)
    await update.message.reply_text(
        f"🗓️ Ringkasan Mingguan:\n📥 Pemasukan: Rp{income:,.0f}\n📤 Pengeluaran: Rp{spending:,.0f}"
    )

async def summary_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(tz).date()
    start_of_month = today.replace(day=1)
    income, spending = get_summary(start_of_month)
    await update.message.reply_text(
        f"📆 Ringkasan Bulanan:\n📥 Pemasukan: Rp{income:,.0f}\n📤 Pengeluaran: Rp{spending:,.0f}"
    )

# Jalankan Bot
app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("saldo", check_balance))
app.add_handler(CommandHandler("harian", summary_today))
app.add_handler(CommandHandler("mingguan", summary_week))
app.add_handler(CommandHandler("bulanan", summary_month))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
