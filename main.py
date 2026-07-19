import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ["BOT_TOKEN"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
TARGET_CHANNEL = os.environ["TARGET_CHANNEL"]
LINK_TEXT = "🆔 @spark_news_tel"

SOURCE_CHANNELS = ["@BadCandom", "@AloNews_com", "@ChizNewz", "@drtel", "@spark_music_tel"]

bot = Client("bot_session", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
userbot = Client("userbot_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

edit_state = {}

@userbot.on_message(filters.chat(SOURCE_CHANNELS))
async def forward_to_bot(client, message):
    try:
        bot_chat = await client.get_chat("@Sparkpaneltelbot")
        await message.forward(chat_id=bot_chat.id)
    except Exception as e:
        print(f"Error: {e}")

@bot.on_message(filters.forwarded & ~filters.user(ADMIN_ID))
async def preview_post(client, message):
    if message.forward_from_chat and message.forward_from_chat.username:
        if message.forward_from_chat.username.lower() in [ch.strip("@").lower() for ch in SOURCE_CHANNELS]:
            original_caption = message.caption or ""
            new_caption = f"{original_caption}\n\n{LINK_TEXT}" if original_caption else LINK_TEXT
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تایید", callback_data=f"approve_{message.id}"),
                 InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{message.id}")]
            ])
            preview_msg = await message.copy(chat_id=ADMIN_ID, caption=new_caption, reply_markup=keyboard)
            edit_state[preview_msg.id] = {
                "original_msg_id": message.id,
                "chat_id": message.chat.id,
                "original_caption": original_caption
            }

@bot.on_callback_query()
async def handle_buttons(client, callback_query):
    data = callback_query.data
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("دسترسی غیرمجاز", show_alert=True)
        return
    if data.startswith("approve_"):
        parts = data.split("_", 1)
        if len(parts) != 2: return
        original_msg_id = int(parts[1])
        info = edit_state.get(callback_query.message.id)
        if not info:
            await callback_query.answer("منقضی شده", show_alert=True)
            return
        final_caption = f"{info['original_caption']}\n\n{LINK_TEXT}" if info['original_caption'] else LINK_TEXT
        try:
            await client.copy_message(TARGET_CHANNEL, info['chat_id'], info['original_msg_id'], caption=final_caption)
            await callback_query.edit_message_caption(caption=f"{callback_query.message.caption}\n\n✅ منتشر شد", reply_markup=None)
        except Exception as e:
            await callback_query.answer(f"خطا: {e}", show_alert=True)
    elif data.startswith("edit_"):
        preview_id = callback_query.message.id
        if preview_id in edit_state:
            edit_state[preview_id]['waiting'] = True
            await callback_query.edit_message_caption(caption=callback_query.message.caption + "\n\n⌨️ کپشن جدید را بفرست:", reply_markup=None)
            await callback_query.answer("کپشن جدید را بفرست")

@bot.on_message(filters.text & filters.user(ADMIN_ID))
async def new_caption(client, message):
    for pid, state in list(edit_state.items()):
        if state.get("waiting"):
            updated_caption = f"{message.text}\n\n{LINK_TEXT}"
            try:
                preview_new = await client.copy_message(ADMIN_ID, state['chat_id'], state['original_msg_id'],
                                                        caption=updated_caption,
                                                        reply_markup=InlineKeyboardMarkup([
                                                            [InlineKeyboardButton("✅ تایید", callback_data=f"approve_{state['original_msg_id']}"),
                                                             InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{state['original_msg_id']}")]
                                                        ]))
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

if __name__ == "__main__":
    import asyncio
    async def main():
        await bot.start()
        await userbot.start()
        print("✅ اجرا شد")
        await asyncio.Event().wait()
    asyncio.run(main())
