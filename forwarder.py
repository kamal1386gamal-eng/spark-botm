import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
BOT_USERNAME = os.environ["BOT_USERNAME"]

# کانال‌های مبدأ (جدید)
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

# صف برای فروارد
forward_queue = asyncio.Queue()

# کارگر صف (یکی‌یکی فروارد می‌کنه)
async def forward_worker():
    while True:
        event = await forward_queue.get()
        try:
            await client.forward_messages(BOT_USERNAME, event.message)
            print(f"📤 فروارد شد از {event.chat.title}")
            await asyncio.sleep(0.5)  # نیم ثانیه فاصله برای جلوگیری از Rate Limit
        except Exception as e:
            print(f"⚠️ خطا در فروارد: {e}")
        finally:
            forward_queue.task_done()

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def new_message_handler(event):
    # پیام جدید رو می‌ذاریم توی صف
    await forward_queue.put(event)

async def main():
    await client.start()
    print("🔥 یوزربات آماده است و این کانال‌ها را زیر نظر دارد:")
    for ch in SOURCE_CHANNELS:
        print(f"   ➜ {ch}")

    # اجرای کارگر صف در پس‌زمینه
    asyncio.create_task(forward_worker())

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
