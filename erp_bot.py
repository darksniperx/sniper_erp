import os
import json
import requests
import zipfile
from bs4 import BeautifulSoup
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

TOKEN = '7840977295:AAEMtl8LNxUaE0m8tkUg6MFVP41ETsmSYn8'
ADMIN_ID = 7730908928
BASE_URL = 'http://erp.imsec.ac.in/export/'

USER_FILE = 'users.json'
BLOCKED_FILE = 'blocked.json'
LOG_FILE = 'logs.txt'

def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return set(json.load(f))
    return default

users = load_data(USER_FILE, set())
blocked = load_data(BLOCKED_FILE, set())

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(list(data), f)

# ⬇️ START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in blocked:
        users.add(uid)
        save_data(USER_FILE, users)

    await update.message.reply_text(
        "🔥 Welcome to *DarkSniperX ERP Data Bot* 🔥\n"
        "Coded by: Sniper\n\n"
        "*Available Commands:*\n"
        "`/getdata` - Get today’s ERP files\n"
        "`/getzip` - Get all files in one ZIP\n"
        "`/feedback <msg>` - Send feedback to admin\n"
        "`/help` - Show this command list again\n\n"
        "*Admin Only Commands:*\n"
        "`/block <user_id>`\n"
        "`/unblock <user_id>`\n"
        "`/broadcast <msg>`\n"
        "`/reply <user_id> <msg>`\n"
        "`/userlist` - Export user IDs\n",
        parse_mode="Markdown"
    )

# ⬇️ HELP
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ⬇️ GET DATA
async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = str(update.effective_user.id)
        if uid in blocked:
            await update.message.reply_text("🚫 You are blocked from using this bot.")
            return

        user = update.effective_user
        username = f"@{user.username}" if user.username else "No username"
        first_name = user.first_name

        log_text = f"👤 Name: {first_name}\n🔗 Username: {username}\n🆔 ID: {uid}\n📌 Command: /getdata"
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"👀 *New Access Alert!*\n\n{log_text}", parse_mode="Markdown")
        with open(LOG_FILE, 'a') as f:
            f.write(log_text + '\n\n')

        today = datetime.now().strftime("%d-%m-%Y")
        await update.message.reply_text(f"💀 *DarkSniper\\_X Activated* 💀\n📅 Date: `{today}`\n📡 Scanning ERP export files...", parse_mode="Markdown")

        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        file_links = [BASE_URL + link['href'] for link in links if link['href'].endswith(('.xlsx', '.csv', '.pdf'))]
        if not file_links:
            await update.message.reply_text("⚠️ No files found.")
            return

        for file_url in file_links:
            file_name = file_url.split("/")[-1]
            file_data = requests.get(file_url).content
            await update.message.reply_document(document=file_data, filename=file_name)

        await update.message.reply_text("✅ *Mission Complete: All files sent.*", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error:\n`{str(e)}`", parse_mode="Markdown")

# ⬇️ GET ZIP
async def get_zip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid in blocked:
        await update.message.reply_text("🚫 You are blocked from using this bot.")
        return

    await update.message.reply_text("📦 Preparing ZIP of ERP files...")
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    file_links = [BASE_URL + link['href'] for link in links if link['href'].endswith(('.xlsx', '.csv', '.pdf'))]

    if not file_links:
        await update.message.reply_text("⚠️ No files found.")
        return

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for file_url in file_links:
            file_name = file_url.split("/")[-1]
            file_content = requests.get(file_url).content
            zip_file.writestr(file_name, file_content)
    zip_buffer.seek(0)
    await update.message.reply_document(document=InputFile(zip_buffer, filename="ERP_Sniper_Data.zip"))

# ⬇️ ADMIN COMMANDS
async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.args:
        blocked.add(context.args[0])
        save_data(BLOCKED_FILE, blocked)
        await update.message.reply_text(f"✅ User `{context.args[0]}` blocked.", parse_mode="Markdown")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if context.args:
        blocked.discard(context.args[0])
        save_data(BLOCKED_FILE, blocked)
        await update.message.reply_text(f"✅ User `{context.args[0]}` unblocked.", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❗ Usage: /broadcast <message>")
        return
    message = ' '.join(context.args)
    sent = 0
    for uid in users:
        if uid not in blocked:
            try:
                await context.bot.send_message(chat_id=int(uid), text=f"📢 *Broadcast:*\n{message}", parse_mode="Markdown")
                sent += 1
            except:
                pass
    await update.message.reply_text(f"📨 Sent to {sent} users.")

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "No username"
    msg = ' '.join(context.args)
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📬 *Feedback Received*\nFrom: {name} ({username})\nID: {uid}\n\nMessage:\n{msg}", parse_mode="Markdown")
    await update.message.reply_text("✅ Feedback sent to admin.")

async def reply_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("❗ Usage: /reply <user_id> <message>")
        return
    uid = context.args[0]
    msg = ' '.join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=int(uid), text=f"📩 *Message from Admin:*\n{msg}", parse_mode="Markdown")
        await update.message.reply_text("✅ Message sent.")
    except:
        await update.message.reply_text("❌ Failed to send message.")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = '\n'.join(users)
    with open('userlist.txt', 'w') as f:
        f.write(data)
    await update.message.reply_document(document=open('userlist.txt', 'rb'))

# ⬇️ MAIN
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("getdata", get_data))
    app.add_handler(CommandHandler("getzip", get_zip))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("reply", reply_user))
    app.add_handler(CommandHandler("userlist", userlist))
    print("🤖 DarkSniper_X Bot is now running...")
    app.run_polling()
