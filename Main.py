import os
import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL

API_ID = 29170645
API_HASH = "0498ddbf04f71f7d91018c27140b82b3"
BOT_TOKEN = "8160147413:AAHwdCB3JUKF_hygM39Ngnc35trjlucfwpA"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ydl_opts = {
    "format": "bestvideo+bestaudio/best",
    "outtmpl": f"{DOWNLOAD_DIR}/%(title).80s.%(ext)s",
    "merge_output_format": "mp4",
    "quiet": True,
    "noplaylist": True,
}

app = Client(
    "yt-dlp-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start(_, msg):
    await msg.reply(
        "📥 **Media Downloader Bot**\n\n"
        "YouTube / X (Twitter) / Instagram\n"
        "Bas link bhejo 👇"
    )

@app.on_message(filters.text & ~filters.command([]))
async def download(_, msg):
    url = msg.text.strip()
    status = await msg.reply("⏳ Download ho raha hai...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if filename.endswith(".webm"):
            filename = filename.replace(".webm", ".mp4")

        await status.edit("📤 Telegram par upload ho raha hai...")
        await msg.reply_video(
            video=filename,
            caption=f"✅ **Downloaded:** {info.get('title')}"
        )

        os.remove(filename)

    except Exception as e:
        await status.edit(f"❌ Error:\n`{e}`")


app.run()
