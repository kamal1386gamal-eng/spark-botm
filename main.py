import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# دریافت اطلاعات از Railway (متغیرهای محیطی)
BOT_TOKEN = os.environ["BOT_TOKEN"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
TARGET_CHANNEL = os.environ["TARGET_CHANNEL"]
LINK_TEXT = "🆔 @spark_news_tel"

# کانال‌های مبدأ که پایش می‌شوند (میتوانی بعداً کم و زیاد کنی)
SOURCE_CHANNELS = ["@BadCandom", "@AloNews_com", "@ChizNewz", "@drtel", "@spark_music_tel"]

# کلاینت بات (پاسخگو به دستورات)
bot = Client("bot_session", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# یوزربات (اکانت شخصی برای رصد کانال‌ها)
userbot = Client("userbot_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# دیکشنری موقت برای ذخیره وضعیت ویرایش
edit_state = {}

# ========== بخش یوزربات ==========
@userbot.on_message(filters.chat(SOURCE_CHANNELS))
async def forward_to_bot(client, message):
    """هر پست جدید در کانال‌های مبدأ را برای ربات فوروارد می‌کند"""
    try:
        # فوروارد مستقیم با یوزرنیم ربات (بدون نیاز به get_chat اضافی)
        await message.forward("@Sparkpaneltelbot")
    except Exception as e:
        print(f"Error forwarding: {e}")

# ========== بخش بات ==========
@bot.on_message(filters.forwarded)
async def preview_post(client, message):
    """دریافت فوروارد و ساخت پیش‌نمایش برای ادمین"""
    if message.forward_from_chat and message.forward_from_chat.username:
        # بررسی اینکه از کانال‌های مبدأ باشد
        if message.forward_from_chat.username.lower() in [ch.strip("@").lower() for ch in SOURCE_CHANNELS]:
            original_caption = message.caption or ""
            new_caption = f"{original_caption}\n\n{LINK_TEXT}" if original_caption else LINK_TEXT

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تایید", callback_data=f"approve_{message.id}"),
                    InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{message.id}")
                ]
            ])

            preview_msg = await message.copy(
                chat_id=ADMIN_ID,
                caption=new_caption,
                reply_markup=keyboard
            )

            edit_state[preview_msg.id] = {
                "original_msg_id": message.id,
                "chat_id": message.chat.id,
                "original_caption": original_caption
            }

@bot.on_callback_query()
async def handle_buttons(client, callback_query):
    """پردازش دکمه‌های تأیید و ویرایش"""
    data = callback_query.data
    user_id = callback_query.from_user.id

    if user_id != ADMIN_ID:
        await callback_query.answer("شما دسترسی ندارید.", show_alert=True)
        return

    if data.startswith("approve_"):
        parts = data.split("_", 1)
        if len(parts) != 2:
            return
        original_msg_id = int(parts[1])
        info = edit_state.get(callback_query.message.id)
        if not info:
            await callback_query.answer("اطلاعات منقضی شده.", show_alert=True)
            return

        final_caption = f"{info['original_caption']}\n\n{LINK_TEXT}" if info['original_caption'] else LINK_TEXT

        try:
            await client.copy_message(
                chat_id=TARGET_CHANNEL,
                from_chat_id=info['chat_id'],
                message_id=info['original_msg_id'],
                caption=final_caption
            )
            await callback_query.edit_message_caption(
                caption=f"{callback_query.message.caption}\n\n✅ منتشر شد",
                reply_markup=None
            )
        except Exception as e:
            await callback_query.answer(f"خطا در انتشار: {e}", show_alert=True)

    elif data.startswith("edit_"):
        preview_id = callback_query.message.id
        if preview_id in edit_state:
            edit_state[preview_id]['waiting'] = True
            await callback_query.edit_message_caption(
                caption=callback_query.message.caption + "\n\n⌨️ کپشن جدید را بفرست:",
                reply_markup=None
            )
            await callback_query.answer("کپشن جدید را بفرست")

@bot.on_message(filters.text & filters.user(ADMIN_ID))
async def receive_new_caption(client, message):
    """دریافت کپشن جدید در حالت ویرایش"""
    for pid, state in list(edit_state.items()):
        if state.get("waiting"):
            updated_caption = f"{message.text}\n\n{LINK_TEXT}"
            try:
                preview_new = await client.copy_message(
                    chat_id=ADMIN_ID,
                    from_chat_id=state['chat_id'],
                    message_id=state['original_msg_id'],
                    caption=updated_caption,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ تایید", callback_data=f"approve_{state['original_msg_id']}"),
                            InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{state['original_msg_id']}")
                        ]
                    ])
                )
                edit_state[preview_new.id] = {
                    "original_msg_id": state['original_msg_id'],
                    "chat_id": state['chat_id'],
                    "original_caption": message.text
                }
                del edit_state[pid]
                await message.delete()
            except Exception as e:
                await message.reply(f"خطا: {e}")
            state['waiting'] = False
            break

# ========== اجرای همزمان ==========
if __name__ == "__main__":
    import asyncio
    async def main():
        await bot.start()
        await userbot.start()
        print("✅ اجرا شد")
        await asyncio.Event().wait()  # برنامه را زنده نگه می‌دارد
    asyncio.run(main())
