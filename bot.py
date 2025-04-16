import os
import telebot
import datetime
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, request

app = Flask(__name__)
bot = telebot.TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

SHEET_NAME = "Catatan Dompet"
SHEET_TAB = "Sheet1"

sheet = client.open(SHEET_NAME).worksheet(SHEET_TAB)

def parse_message(message):
    try:
        parts = message.split(',')
        if len(parts) != 2:
            return None, None
        keterangan = parts[0].strip()
        jumlah = int(parts[1].strip())
        return keterangan, jumlah
    except:
        return None, None

def calculate_total():
    records = sheet.get_all_values()[1:]  # skip header
    total = 0
    for row in records:
        try:
            jumlah_str = row[2]  # kolom ke-3 = 'Jumlah'
            jumlah = (
                str(jumlah_str)
                .replace("Rp", "")
                .replace(".", "")
                .replace(",", "")
                .strip()
            )
            total += int(jumlah)
        except Exception as e:
            print(f"Error parsing jumlah: {e}")
            continue
    return total

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    keterangan, jumlah = parse_message(text)
    if keterangan is None or jumlah is None:
        bot.reply_to(message, "Format salah. Gunakan format: Keterangan, Jumlah")
        return

    tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([tanggal, keterangan, jumlah])

    total = calculate_total()
    formatted = f"Rp{jumlah:,.0f}".replace(",", ".")
    formatted_total = f"Rp{total:,.0f}".replace(",", ".")

    bot.reply_to(
        message,
        f"Tercatat: {keterangan} - {formatted}\nTotal pengeluaran: {formatted_total}"
    )

@app.route("/" + os.environ['TELEGRAM_BOT_TOKEN'], methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "Bot aktif!"

if __name__ == "__main__":
    app.run(debug=True)
