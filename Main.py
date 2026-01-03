import os
import re
import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# ───────── CONFIG ─────────
API_ID = 29170645
API_HASH = "0498ddbf04f71f7d91018c27140b82b3"
BOT_TOKEN = "8160147413:AAHwdCB3JUKF_hygM39Ngnc35trjlucfwpA"

DOWNLOAD_DIR = "downloads"
COOKIE_FILE = "cookies.txt"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ───────── HELPERS ─────────
def safe_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name)

def cookies_available() -> bool:
    return os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 100

# ───────── yt-dlp OPTIONS ─────────
ydl_opts = {
    "format": "bestvideo+bestaudio/best",
    "outtmpl": f"{DOWNLOAD_DIR}/%(title).80s.%(ext)s",
    "merge_output_format": "mp4",
    "noplaylist": True,
    "quiet": True,
    "retries": 3,
    "user_agent": "Mozilla/5.0",
}

if cookies_available():
    ydl_opts["cookiefile"] = COOKIE_FILE

# ───────── BOT ─────────
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
        "Supports:\n"
        "• YouTube\n"
        "• X (Twitter)\n"
        "• Instagram\n\n"
        "Bas link bhejo 👇"
    )

@app.on_message(filters.text & ~filters.command([]))
async def download(_, msg):
    url = msg.text.strip()
    status = await msg.reply("⏳ Download ho raha hai...")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, fetch_media, url)

        filename = info["file"]
        title = info["title"]

        await status.edit("📤 Telegram par upload ho raha hai...")

        if os.path.getsize(filename) > 2 * 1024 * 1024 * 1024:
            await status.edit("❌ File 2GB se badi hai, upload nahi ho sakti.")
            os.remove(filename)
            return

        await msg.reply_video(
            video=filename,
            caption=f"✅ **Downloaded:** {title}"
        )

        os.remove(filename)

    except DownloadError as e:
        if "Sign in" in str(e) or "cookies" in str(e):
            await status.edit(
                "🔒 **Login required / Cookies expired**\n\n"
                "👉 X (Twitter) ke liye nayi `cookies.txt` export karo"
            )
        else:
            await status.edit(f"❌ Download error:\n`{e}`")

    except Exception as e:
        await status.edit(f"❌ Error:\n`{e}`")

# ───────── DOWNLOAD FUNCTION ─────────
def fetch_media(url: str):
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if "entries" in info:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)

        if filename.endswith(".webm"):
            filename = filename.replace(".webm", ".mp4")

        new_name = safe_name(os.path.basename(filename))
        final_path = os.path.join(DOWNLOAD_DIR, new_name)

        if filename != final_path:
            os.rename(filename, final_path)

        return {
            "file": final_path,
            "title": info.get("title", "Unknown")
        }

# ───────── RUN ─────────
app.run()

