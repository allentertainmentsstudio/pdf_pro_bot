import os
import shutil
import threading

from pyrogram import Client, filters

from config import API_ID, API_HASH, BOT_TOKEN
from admin import is_admin
from database import (
    add_user, inc_files, get_user_count,
    ban_user, unban_user, is_banned
)

from utils.zip import extract_zip
from utils.pdf import images_to_pdf
from utils.ocr import image_to_text, pdf_to_text

from web import app as flask_app


app = Client("pdf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

BASE = "temp"
os.makedirs(BASE, exist_ok=True)

MAINTENANCE = False


# ---------------- START ---------------- #
@app.on_message(filters.command("start"), group=0)
async def start(_, msg):
    add_user(msg.from_user.id, msg.from_user.first_name)

    await msg.reply_text(
        "**✨ What I Can Do for You 🤖**\n\n"
        "🎯 Convert images into high-quality PDFs\n"
        "📦 Compress & optimize files\n"
        "✂️ Split or merge PDFs\n"
        "🔐 Secure documents\n"
        "📄 Extract text from PDFs\n\n"
        "💡 Send a file to get started!\n"
        "📚 Use /ocr to extract text",
        disable_web_page_preview=True
    )


# ---------------- BAN + MAINTENANCE CHECK ---------------- #
@app.on_message(filters.all, group=1)
async def check(_, msg):
    global MAINTENANCE

    if msg.from_user:
        if is_banned(msg.from_user.id):
            await msg.reply("🚫 You are banned from using this bot")
            return

        if MAINTENANCE and not is_admin(msg.from_user.id):
            await msg.reply("⚠️ Bot under maintenance")
            return


# ---------------- FILE HANDLER ---------------- #
@app.on_message(filters.document | filters.photo, group=2)
async def handle(client, message):
    try:
        add_user(message.from_user.id, message.from_user.first_name)

        path = await message.download(file_name=BASE)
        user_dir = os.path.join(BASE, str(message.from_user.id))
        os.makedirs(user_dir, exist_ok=True)

        status = await message.reply("⏳ Processing...")

        # IMAGE → PDF
        if path.lower().endswith((".jpg", ".jpeg", ".png")):
            output = os.path.join(user_dir, "output.pdf")
            result = images_to_pdf([path], output)

            if result:
                inc_files(message.from_user.id)
                await status.edit("✅ PDF Ready")
                await message.reply_document(result)

        # ZIP → PDF
        elif path.lower().endswith(".zip"):
            extract_zip(path, user_dir)
            output = os.path.join(user_dir, "output.pdf")
            result = images_to_pdf(user_dir, output)

            if result:
                inc_files(message.from_user.id)
                await status.edit("✅ PDF Ready")
                await message.reply_document(result)

        else:
            await status.edit("❌ Unsupported file")

    except Exception as e:
        await message.reply(f"❌ Error: {e}")

    finally:
        shutil.rmtree(user_dir, ignore_errors=True)
        if os.path.exists(path):
            os.remove(path)


# ---------------- OCR ---------------- #
@app.on_message(filters.command("ocr"), group=2)
async def ocr_cmd(_, msg):
    try:
        if not msg.reply_to_message:
            return await msg.reply("❌ Reply to image or PDF")

        await msg.reply("⏳ Extracting text...")

        file = await msg.reply_to_message.download(file_name=BASE)

        if file.lower().endswith((".jpg", ".png", ".jpeg")):
            text = image_to_text(file)

        elif file.lower().endswith(".pdf"):
            text = pdf_to_text(file)

        else:
            return await msg.reply("❌ Unsupported file")

        out = file + ".txt"

        with open(out, "w", encoding="utf-8") as f:
            f.write(text)

        await msg.reply_document(out, caption="📄 OCR Result")

    except Exception as e:
        await msg.reply(f"❌ Error: {e}")

    finally:
        if os.path.exists(file):
            os.remove(file)
        if os.path.exists(file + ".txt"):
            os.remove(file + ".txt")


# ---------------- ADMIN ---------------- #
@app.on_message(filters.command("stats"), group=2)
async def stats(_, msg):
    if not is_admin(msg.from_user.id):
        return
    await msg.reply(f"📊 Users: {get_user_count()}")


@app.on_message(filters.command("ban"), group=2)
async def ban_cmd(_, msg):
    if not is_admin(msg.from_user.id):
        return

    if len(msg.command) < 2:
        return await msg.reply("❌ Provide user ID")

    user_id = int(msg.command[1])
    ban_user(user_id)
    await msg.reply("🚫 User banned")


@app.on_message(filters.command("unban"), group=2)
async def unban_cmd(_, msg):
    if not is_admin(msg.from_user.id):
        return

    if len(msg.command) < 2:
        return await msg.reply("❌ Provide user ID")

    user_id = int(msg.command[1])
    unban_user(user_id)
    await msg.reply("✅ User unbanned")


@app.on_message(filters.command("maintenance"), group=2)
async def maintenance(_, msg):
    global MAINTENANCE
    if not is_admin(msg.from_user.id):
        return

    MAINTENANCE = not MAINTENANCE
    await msg.reply(f"⚙️ Maintenance: {MAINTENANCE}")


# ---------------- RUN ---------------- #
def run_bot():
    app.run()


def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_bot).start()
