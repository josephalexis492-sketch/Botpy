import json
import logging
import time
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8237376549:AAHA_xlxX6e4FLqvnwoOi_zgzi10t_mFUFM"
OWNER_ID = 6548935235
DATA_FILE = "data.json"

logging.basicConfig(level=logging.INFO)

# ================= LOAD / SAVE =================
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "key": None,
            "expiry": None,
            "apk": None,
            "virtual": None,
            "warns": {}
        }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data_store = load_data()

# ================= OWNER SAVE SYSTEM =================
async def save_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    msg = update.message

    # ===== SAVE KEY WITH EXPIRY =====
    if msg.text and not msg.text.startswith("/"):
        try:
            key_part, days_part = msg.text.split("|")
            key = key_part.strip()
            days = int(days_part.strip())

            expiry_date = datetime.now() + timedelta(days=days)

            # Overwrite old key automatically
            data_store["key"] = key
            data_store["expiry"] = expiry_date.timestamp()

            save_data(data_store)

            await msg.reply_text(
                f"✅ New Key Saved!\n\n"
                f"🔐 Key: {key}\n"
                f"📅 Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except:
            await msg.reply_text(
                "❌ Format wrong.\nUse:\nKEY | DAYS\n\nExample:\nVIP-123 | 7"
            )

    # ===== SAVE DOCUMENTS =====
    elif msg.document:
        caption = msg.caption.lower() if msg.caption else ""

        if caption == "injc":
            data_store["apk"] = msg.document.file_id
            save_data(data_store)
            await msg.reply_text("✅ APK saved!")

        elif caption == "virtual":
            data_store["virtual"] = msg.document.file_id
            save_data(data_store)
            await msg.reply_text("✅ Virtual saved!")

# ================= KEY COMMAND =================
async def send_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data_store["key"]:
        await update.message.reply_text("❌ No key set.")
        return

    # Check expiry
    if data_store["expiry"]:
        if time.time() > data_store["expiry"]:
            await update.message.reply_text("❌ Key expired.")
            return

    await update.message.reply_text(
        f"🔐 VIP KEY:\n\n{data_store['key']}"
    )

# ================= STATUS COMMAND =================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data_store["key"]:
        await update.message.reply_text("❌ No key available.")
        return

    expiry_timestamp = data_store["expiry"]

    if not expiry_timestamp:
        await update.message.reply_text("⚠️ No expiry set.")
        return

    now = time.time()

    if now > expiry_timestamp:
        await update.message.reply_text(
            "❌ Key Status: EXPIRED"
        )
    else:
        remaining = int((expiry_timestamp - now) // 86400)
        expiry_date = datetime.fromtimestamp(expiry_timestamp)

        await update.message.reply_text(
            f"✅ Key Status: ACTIVE\n\n"
            f"📅 Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⏳ Days Remaining: {remaining}"
        )

# ================= APK =================
async def send_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if data_store["apk"]:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=data_store["apk"]
        )
    else:
        await update.message.reply_text("❌ No APK uploaded.")

# ================= VIRTUAL =================
async def send_virtual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if data_store["virtual"]:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=data_store["virtual"]
        )
    else:
        await update.message.reply_text("❌ No virtual uploaded.")

# ================= WARN =================
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    user_id = str(user.id)

    warns = data_store["warns"]
    warns[user_id] = warns.get(user_id, 0) + 1

    save_data(data_store)

    if warns[user_id] >= 3:
        await context.bot.ban_chat_member(
            update.effective_chat.id,
            user.id
        )
        await update.message.reply_text(
            f"🚫 {user.first_name} banned (3 warns)"
        )
    else:
        await update.message.reply_text(
            f"⚠️ {user.first_name} warned ({warns[user_id]}/3)"
        )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & (filters.TEXT | filters.Document.ALL),
            save_private
        )
    )

    app.add_handler(CommandHandler("key", send_key))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("injc", send_apk))
    app.add_handler(CommandHandler("virtual", send_virtual))
    app.add_handler(CommandHandler("warn", warn))

    print("🔥 Upgraded key system running...")
    app.run_polling()

if __name__ == "__main__":
    main()