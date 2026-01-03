import os
import re
import json
import time
import asyncio
import shutil
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# ───────── CONFIG ─────────
API_ID = 29170645
API_HASH = "0498ddbf04f71f7d91018c27140b82b3"
BOT_TOKEN = "8160147413:AAHwdCB3JUKF_hygM39Ngnc35trjlucfwpA"

ADMIN_IDS = [6558799817, 6369434417]

DOWNLOAD_DIR = "downloads"
COOKIES_DIR = "cookies"
DISABLED_DIR = "cookies/disabled"
STATS_FILE = "cookies/cookie_stats.json"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)
os.makedirs(DISABLED_DIR, exist_ok=True)

# ───────── STATS INIT ─────────
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        json.dump({}, f)

# ───────── HELPERS ─────────
def safe_name(name: str):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def load_stats():
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def update_stats(cookie, success):
    stats = load_stats()
    name = os.path.basename(cookie)

    stats.setdefault(name, {
        "used": 0,
        "failed": 0,
        "last_used": None
    })

    stats[name]["used"] += 1
    if not success:
        stats[name]["failed"] += 1

    stats[name]["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_stats(stats)

def disable_cookie(cookie):
    name = os.path.basename(cookie)
    shutil.move(cookie, os.path.join(DISABLED_DIR, name))

def notify_admins(text):
    for admin in ADMIN_IDS:
        try:
            asyncio.run(app.send_message(admin, text))
        except Exception:
            pass

def get_active_cookies():
    return [
        os.path.join(COOKIES_DIR, f)
        for f in os.listdir(COOKIES_DIR)
        if f.endswith(".txt")
    ]

# ───────── yt-dlp OPTIONS ─────────
BASE_YDL_OPTS = {
    "format": "bestvideo+bestaudio/best",
    "outtmpl": f"{DOWNLOAD_DIR}/%(title).80s.%(ext)s",
    "merge_output_format": "mp4",
    "noplaylist": True,
    "quiet": True,
    "retries": 3,
    "user_agent": "Mozilla/5.0",
}

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
        "📥 **Advanced Media Downloader Bot**\n\n"
        "Features:\n"
        "• Cookies auto-rotation\n"
        "• Auto-disable expired cookies\n"
        "• Cookie usage stats\n"
        "• Public → Private fallback\n\n"
        "Bas link bhejo 👇"
    )

@app.on_message(filters.text & ~filters.command([]))
async def download(_, msg):
    url = msg.text.strip()
    status = await msg.reply("⏳ Download ho raha hai...")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, smart_download, url)

        file = info["file"]
        title = info["title"]

        await status.edit("📤 Upload ho raha hai...")

        if os.path.getsize(file) > 2 * 1024 * 1024 * 1024:
            await status.edit("❌ File 2GB se badi hai.")
            os.remove(file)
            return

        await msg.reply_video(file, caption=f"✅ **Downloaded:** {title}")
        os.remove(file)

    except Exception as e:
        await status.edit(f"❌ Error:\n`{e}`")

# ───────── SMART DOWNLOAD ─────────
def smart_download(url):
    # 1️⃣ Try public
    try:
        return fetch_media(url, None)
    except Exception:
        pass

    # 2️⃣ Cookies rotation
    cookies = get_active_cookies()
    if not cookies:
        raise Exception("No active cookies available")

    for cookie in cookies:
        try:
            result = fetch_media(url, cookie)
            update_stats(cookie, True)
            return result

        except DownloadError as e:
            update_stats(cookie, False)

            if "Sign in" in str(e) or "cookie" in str(e):
                disable_cookie(cookie)
                notify_admins(
                    f"🚫 **Cookie disabled (expired)**\n\n`{os.path.basename(cookie)}`"
                )
                continue
            else:
                raise e

    raise Exception("All cookies expired")

# ───────── FETCH MEDIA ─────────
def fetch_media(url, cookie_file):
    opts = BASE_YDL_OPTS.copy()
    if cookie_file:
        opts["cookiefile"] = cookie_file

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if "entries" in info:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)

        if filename.endswith(".webm"):
            filename = filename.replace(".webm", ".mp4")

        final = safe_name(os.path.basename(filename))
        final_path = os.path.join(DOWNLOAD_DIR, final)

        if filename != final_path:
            os.rename(filename, final_path)

        return {
            "file": final_path,
            "title": info.get("title", "Unknown")
        }

# ───────── RUN ─────────
app.run()
