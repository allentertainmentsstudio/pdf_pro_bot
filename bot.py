import os
import shutil
import threading

from pyrogram import Client, filters

from config import API_ID, API_HASH, BOT_TOKEN
from admin import is_admin
from database import add_user, inc_files, get_user_count

from utils.zip import extract_zip
from utils.pdf import images_to_pdf
from utils.ocr import image_to_text, pdf_to_text

from web import app as flask_app


app = Client("pdf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

BASE = "temp"
os.makedirs(BASE, exist_ok=True)

MAINTENANCE = False


# ---------------- START ---------------- #
@app.on_message(filters.command("start"))
async def start(_, msg):
    add_user(msg.from_user.id, msg.from_user.first_name)

    await msg.reply_text(
        """✨ PDF Pro Bot ✨

📸 Images → PDF
📦 ZIP → PDF
🧠 OCR → Text extraction

Send file to start 🚀"""
    )


# ---------------- MAINTENANCE CHECK ---------------- #
@app.on_message()
async def check(_, msg):
    global MAINTENANCE
    if MAINTENANCE and not is_admin(msg.from_user.id):
        return await msg.reply("⚠️ Bot under maintenance")


# ---------------- FILE HANDLER ---------------- #
@app.on_message(filters.document)
async def handle(client, message):

    add_user(message.from_user.id, message.from_user.first_name)

    path = await message.download(file_name=BASE)
    user_dir = os.path.join(BASE, str(message.from_user.id))
    os.makedirs(user_dir, exist_ok=True)

    status = await message.reply("⏳ Processing...")

    if path.endswith(".zip"):
        extract_zip(path, user_dir)
        output = os.path.join(user_dir, "output.pdf")
        result = images_to_pdf(user_dir, output)

        if result:
            inc_files(message.from_user.id)
            await message.reply_document(result, caption="✅ PDF Ready")

    else:
        await status.edit("❌ Only ZIP supported")

    shutil.rmtree(user_dir, ignore_errors=True)
    os.remove(path)


# ---------------- OCR COMMAND ---------------- #
@app.on_message(filters.command("ocr"))
async def ocr_cmd(client, message):

    if not message.reply_to_message:
        return await message.reply("❌ Reply to file")

    file = await message.reply_to_message.download(file_name=BASE)

    await message.reply("🧠 Extracting text...")

    text = ""

    if file.endswith((".jpg", ".jpeg", ".png")):
        text = image_to_text(file)

    elif file.endswith(".pdf"):
        text = pdf_to_text(file)

    else:
        return await message.reply("❌ Unsupported file")

    txt_file = file + ".txt"

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(text)

    await message.reply_document(txt_file, caption="📄 OCR Result")

    os.remove(file)
    os.remove(txt_file)


# ---------------- ADMIN ---------------- #
@app.on_message(filters.command("stats"))
async def stats(_, msg):
    if not is_admin(msg.from_user.id):
        return

    await msg.reply(f"📊 Users: {get_user_count()}")


@app.on_message(filters.command("maintenance"))
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
    t1 = threading.Thread(target=run_flask)
    t2 = threading.Thread(target=run_bot)

    t1.start()
    t2.start()
