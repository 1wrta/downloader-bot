import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import yt_dlp

TOKEN = '8627651088:AAHx-66uY9amd9c3ggJ6XjPhzEXgZfonpkc'

user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'هلا بيك! 👋\n\nدزلي رابط من:\n'
        '• يوتيوب\n• إنستغرام\n• تيك توك\n\n'
        'وراح تختار: فيديو (MP4) أو صوت (MP3)'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith('http'):
        await update.message.reply_text('أرسل رابطاً صالحاً يبدأ بـ http')
        return

    user_urls[update.effective_user.id] = url

    keyboard = [
        [
            InlineKeyboardButton("فيديو (MP4)", callback_data="mp4"),
            InlineKeyboardButton("صوت (MP3)", callback_data="mp3"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('اختر نوع التحميل:', reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_urls.get(user_id)

    if not url:
        await query.edit_message_text('انتهت الجلسة، أرسل الرابط مرة ثانية.')
        return

    download_type = query.data
    await query.edit_message_text('جاري التحميل... ⏳')

    output_file = f'dl_{user_id}'

    if download_type == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_file + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_file + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if download_type == 'mp3':
            filename = output_file + '.mp3'

        if not os.path.exists(filename):
            for f in os.listdir('.'):
                if f.startswith(output_file):
                    filename = f
                    break

        if download_type == 'mp3':
            await query.message.reply_audio(
                audio=open(filename, 'rb'),
                caption='تفضل الصوت مالتك ✅',
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60,
            )
        else:
            await query.message.reply_video(
                video=open(filename, 'rb'),
                caption='تفضل الفيديو مالتك ✅',
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60,
            )

        os.remove(filename)
        await query.edit_message_text('تم التحميل ✅')

    except Exception as e:
        await query.edit_message_text(f'صار خطأ: {str(e)}')
        for f in os.listdir('.'):
            if f.startswith(output_file):
                os.remove(f)

def main():
    request = HTTPXRequest(
        read_timeout=120,
        write_timeout=120,
        connect_timeout=60,
    )
    application = Application.builder().token(TOKEN).request(request).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    print("البوت شغال الآن... بانتظار الروابط.")
    application.run_polling()

if __name__ == '__main__':
    main()
