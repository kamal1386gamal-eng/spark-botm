import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
BOT_USERNAME = os.environ["BOT_USERNAME"]

SOURCE_CHANNELS = [
    "@IrJaavan",
    "@khabarfuri",
    "@ChizNewz",
    "@ChizBergerz",
    "@drtel",
    "@FarsKhabari",
    "@spark_music_tel",
]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# صف برای پست‌های تکی
forward_queue = asyncio.Queue()

# جمع‌آوری آلبوم‌ها (کلید = grouped_id)
pending_albums = {}

async def forward_single_worker():
    """فروارد پست‌های تکی با فاصلهٔ نیم ثانیه"""
    while True:
        event = await forward_queue.get()
        try:
            await client.forward_messages(BOT_USERNAME, event.message)
            print(f"📤 فروارد تکی از {event.chat.title}")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ خطا در فروارد تکی: {e}")
        finally:
            forward_queue.task_done()

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def new_message_handler(event):
    grouped_id = event.message.grouped_id
    if grouped_id:
        # پیام متعلق به یک آلبوم است
        if grouped_id not in pending_albums:
            pending_albums[grouped_id] = {"messages": [], "timer": None}
        pending_albums[grouped_id]["messages"].append(event)

        if not pending_albums[grouped_id]["timer"]:
            async def process_album_later(gid=grouped_id):
                await asyncio.sleep(1.5)  # کمی صبر برای دریافت همهٔ آیتم‌ها
                album = pending_albums.pop(gid, None)
                if not album:
                    return
                msgs = album["messages"]
                msgs.sort(key=lambda m: m.message.id)
                # استخراج شناسهٔ عددی پیام‌ها
                msg_ids = [m.message.id for m in msgs]
                # از اولین پیام، شناسهٔ چت مبدأ را می‌گیریم
                from_peer = msgs[0].chat_id
                try:
                    # فروارد کل آلبوم در یک درخواست (حفظ گروه‌بندی)
                    await client.forward_messages(BOT_USERNAME, msg_ids, from_peer=from_peer)
                    print(f"📸 آلبوم با {len(msgs)} آیتم فروارد شد")
                except Exception as e:
                    print(f"⚠️ خطا در فروارد آلبوم: {e}")

            pending_albums[grouped_id]["timer"] = asyncio.create_task(process_album_later())
    else:
        # پست تکی → به صف اضافه شود
        await forward_queue.put(event)

async def main():
    await client.start()
    print("🔥 یوزربات آماده است و این کانال‌ها را زیر نظر دارد:")
    for ch in SOURCE_CHANNELS:
        print(f"   ➜ {ch}")

    # اجرای کارگر صف
    asyncio.create_task(forward_single_worker())

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
