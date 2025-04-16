import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Catatan Dompet").sheet1  # Ganti dengan nama sheet kamu

# Logging
logging.basicConfig(level=logging.INFO)

# Bot Logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirim pengeluaranmu dengan format: Keterangan, Jumlah\nContoh: Ayam Goreng, 20000")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "," not in text:
        await update.message.reply_text("Format salah. Gunakan format: Keterangan, Jumlah")
        return

    try:
        keterangan, jumlah = map(str.strip, text.split(",", 1))
        jumlah = int(jumlah.replace(".", "").replace(",", ""))
        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([tanggal, keterangan, jumlah])

        records = sheet.get_all_records()
        total = sum([r['Jumlah'] for r in records if isinstance(r['Jumlah'], int)])
        await update.message.reply_text(f"Tercatat: {keterangan} - Rp{jumlah:,}\nTotal pengeluaran: Rp{total:,}")
    except Exception as e:
        await update.message.reply_text(f"Terjadi error: {e}")

# Main
if __name__ == "__main__":
    TOKEN = os.environ.get("BOT_TOKEN")  # Ambil dari environment variable di Render
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot jalan...")
    app.run_polling()
