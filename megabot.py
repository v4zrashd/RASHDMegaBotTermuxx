#!/data/data/com.termux/files/usr/bin/python
# ============================================================
#  V4Z MEGA BOT — by V4Z RASHD
#  All-in-one Telegram bot: downloads, prayer times,
#  currency, QR, passwords & more.
#  Repo: https://github.com/v4zrashd/RASHDMegaBotTermuxx
#  Channel: https://t.me/rashdteem
# ============================================================
import asyncio
import json
import logging
import os
import secrets
import string
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN_FILE = os.path.expanduser("~/.v4zmegabot/token")
TG_CHANNEL = "https://t.me/rashdteem"
BRAND = "V4Z RASHD"

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("v4zmegabot")

# user_id -> {"awaiting": "link"|"fx"|"qr"}
STATE = {}


def get_token() -> str:
    t = os.environ.get("V4ZMB_TOKEN", "").strip()
    if t:
        return t
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE).read().strip()
    return ""


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬇️ Download", callback_data="m_dl"),
             InlineKeyboardButton("🕌 Prayer", callback_data="m_prayer")],
            [InlineKeyboardButton("💱 Currency", callback_data="m_fx"),
             InlineKeyboardButton("⬛ QR Code", callback_data="m_qr")],
            [InlineKeyboardButton("🔑 Password", callback_data="m_pass"),
             InlineKeyboardButton("🆔 My ID", callback_data="m_id")],
            [InlineKeyboardButton("📢 Channel", url=TG_CHANNEL),
             InlineKeyboardButton("❓ Help", callback_data="m_help")],
        ]
    )


WELCOME = (
    "⚡ <b>V4Z MEGA BOT</b> ⚡\n\n"
    "I'm your all-in-one assistant, by <b>V4Z RASHD</b>.\n"
    "Pick something below 👇"
)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    STATE.pop(update.effective_user.id, None)
    await update.message.reply_text(WELCOME, parse_mode="HTML", reply_markup=main_menu())


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Commands</b>\n\n"
        "/start — main menu\n"
        "/dl — download video/audio from a link\n"
        "/prayer — today's Dhaka prayer times\n"
        "/currency — convert money to BDT (e.g. <code>/currency 100 USD</code>)\n"
        "/qr — make a QR code (e.g. <code>/qr hello</code>)\n"
        "/pass — generate a strong password\n"
        "/id — show your Telegram ID\n\n"
        f"📢 Channel: {TG_CHANNEL}",
        parse_mode="HTML",
    )


async def cmd_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f"🆔 Your ID: <code>{u.id}</code>", parse_mode="HTML")


async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data == "m_dl":
        STATE[uid] = {"awaiting": "link"}
        await q.message.reply_text("🔗 Send me a video link (YouTube / Facebook / Instagram / TikTok...)")
    elif data == "m_prayer":
        await send_prayer(q.message)
    elif data == "m_fx":
        STATE[uid] = {"awaiting": "fx"}
        await q.message.reply_text("💱 Send amount like: <code>100 USD</code>", parse_mode="HTML")
    elif data == "m_qr":
        STATE[uid] = {"awaiting": "qr"}
        await q.message.reply_text("⬛ Send the text or link for the QR code:")
    elif data == "m_pass":
        await q.message.reply_text(f"🔑 <code>{gen_password()}</code>", parse_mode="HTML")
    elif data == "m_id":
        await q.message.reply_text(f"🆔 Your ID: <code>{uid}</code>", parse_mode="HTML")
    elif data == "m_help":
        await q.message.reply_text("Use /help to see all commands.")
    elif data in ("dl_video", "dl_audio"):
        st = STATE.get(uid, {})
        url = st.get("url")
        if not url:
            await q.message.reply_text("Send /dl first, then the link.")
            return
        STATE.pop(uid, None)
        await q.message.reply_text("⏳ Downloading... (max ~45MB for Telegram)")
        try:
            path, title = await asyncio.to_thread(dl_media, url, data == "dl_audio")
            caption = f"✅ {title}\n— via V4Z MEGA BOT"
            with open(path, "rb") as f:
                if data == "dl_audio":
                    await q.message.reply_audio(f, caption=caption)
                else:
                    await q.message.reply_video(f, caption=caption, supports_streaming=True)
        except Exception as e:
            log.warning("download failed: %s", e)
            await q.message.reply_text("❌ Download failed. Try another link (file may exceed 45MB).")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    st = STATE.pop(uid, None)

    if not st:
        # quick commands via plain text
        if text.startswith("/"):
            return
        await update.message.reply_text("Use /start to open the menu ⚡")
        return

    if st["awaiting"] == "link":
        if not text.startswith("http"):
            await update.message.reply_text("❌ That doesn't look like a link. Try /dl again.")
            return
        STATE[uid] = {"awaiting": "fmt", "url": text}
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🎬 Video (MP4)", callback_data="dl_video"),
              InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio")]]
        )
        await update.message.reply_text("Choose format:", reply_markup=kb)
    elif st["awaiting"] == "fx":
        await send_fx(update.message, text)
    elif st["awaiting"] == "qr":
        await send_qr(update.message, text)


# ---------------- features ----------------

def gen_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def http_json(url: str, timeout: int = 15):
    req = urllib.request.Request(url, headers={"User-Agent": "V4ZMegaBot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


async def send_prayer(message):
    try:
        day = datetime.now().strftime("%d-%m-%Y")
        url = f"https://api.aladhan.com/v1/timingsByCity/{day}?city=Dhaka&country=Bangladesh&method=1"
        d = await asyncio.to_thread(http_json, url)
        t = d["data"]["timings"]
        rows = [("🌅 Fajr", t["Fajr"]), ("🌞 Sunrise", t["Sunrise"]), ("☀️ Dhuhr", t["Dhuhr"]),
                ("🌤️ Asr", t["Asr"]), ("🌇 Maghrib", t["Maghrib"]), ("🌙 Isha", t["Isha"])]
        txt = "🕌 <b>Dhaka Prayer Times</b> — " + day + "\n\n"
        txt += "\n".join(f"{n}: <b>{v[:5]}</b>" for n, v in rows)
        await message.reply_text(txt, parse_mode="HTML")
    except Exception as e:
        log.warning("prayer failed: %s", e)
        await message.reply_text("❌ Couldn't fetch prayer times right now.")


async def send_fx(message, text: str):
    try:
        parts = text.upper().split()
        amount = float(parts[0])
        frm = parts[1] if len(parts) > 1 else "USD"
        url = f"https://api.frankfurter.app/latest?from={urllib.parse.quote(frm)}&to=BDT"
        d = await asyncio.to_thread(http_json, url)
        rate = d["rates"]["BDT"]
        total = amount * rate
        await message.reply_text(
            f"💱 <b>{amount:g} {frm}</b> = <b>{total:,.2f} BDT</b>\n"
            f"<i>1 {frm} = {rate:,.2f} BDT</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        log.warning("fx failed: %s", e)
        await message.reply_text("❌ Usage: <code>100 USD</code>", parse_mode="HTML")


async def send_qr(message, text: str):
    try:
        import qrcode
        img = qrcode.make(text)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f.name)
            path = f.name
        with open(path, "rb") as f:
            await message.reply_photo(f, caption="⬛ QR ready — V4Z MEGA BOT")
        os.unlink(path)
    except Exception as e:
        log.warning("qr failed: %s", e)
        await message.reply_text("❌ QR failed. Is the 'qrcode' package installed?")


def dl_media(url: str, audio_only: bool):
    import yt_dlp
    tmp = tempfile.mkdtemp(prefix="v4zmb_")
    opts = {
        "outtmpl": os.path.join(tmp, "%(title).50s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if audio_only:
        opts.update({
            "format": "ba/b",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}],
        })
    else:
        opts.update({
            "format": "bv*[filesize<45M]+ba/b[filesize<45M]/b[filesize<45M]",
            "merge_output_format": "mp4",
        })
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "media")
        fname = ydl.prepare_filename(info)
        if audio_only:
            base, _ = os.path.splitext(fname)
            for cand in (base + ".mp3", fname):
                if os.path.exists(cand):
                    return cand, title
        if os.path.exists(fname):
            return fname, title
    # fallback: whatever landed in tmp
    for f in os.listdir(tmp):
        return os.path.join(tmp, f), title
    raise Runtime


async def cmd_dl(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    STATE[update.effective_user.id] = {"awaiting": "link"}
    await update.message.reply_text("🔗 Send me a video link (YouTube / Facebook / Instagram / TikTok...)")


async def cmd_prayer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await send_prayer(update.message)


async def cmd_fx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    arg = " ".join(ctx.args) if ctx.args else ""
    if not arg:
        STATE[update.effective_user.id] = {"awaiting": "fx"}
        await update.message.reply_text("💱 Send amount like: <code>100 USD</code>", parse_mode="HTML")
    else:
        await send_fx(update.message, arg)


async def cmd_qr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    arg = " ".join(ctx.args) if ctx.args else ""
    if not arg:
        STATE[update.effective_user.id] = {"awaiting": "qr"}
        await update.message.reply_text("⬛ Send the text or link for the QR code:")
    else:
        await send_qr(update.message, arg)


async def cmd_pass(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🔑 <code>{gen_password()}</code>", parse_mode="HTML")


def main():
    token = get_token()
    if not token:
        print("❌ No bot token found.")
        print("   Get one from @BotFather, then run: v4zmegabot --set-token")
        raise SystemExit(1)
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("dl", cmd_dl))
    app.add_handler(CommandHandler("prayer", cmd_prayer))
    app.add_handler(CommandHandler("currency", cmd_fx))
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CommandHandler("pass", cmd_pass))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("⚡ V4Z MEGA BOT is running... (Ctrl+C to stop)")
    app.run_polling()


if __name__ == "__main__":
    main()
