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

# صف برای پست‌های تکی (غیر آلبوم)
forward_queue = asyncio.Queue()

# جمع‌آوری آلبوم‌ها (کلید = media_group_id)
pending_albums = {}

async def forward_single_worker():
    """کارگر صف برای فروارد پست‌های تکی با فاصله"""
    while True:
        event = await forward_queue.get()
        try:
            await client.forward_messages(BOT_USERNAME, event.message)
            print(f"📤 فروارد تکی از {event.chat.title}")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ خطا در فروارد: {e}")
        finally:
            forward_queue.task_done()

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def new_message_handler(event):
    if event.message.media_group_id:
        # بخشی از یک آلبوم است → جمع‌آوری شود
        group_id = event.message.media_group_id
        if group_id not in pending_albums:
            pending_albums[group_id] = {"messages": [], "timer": None}
        pending_albums[group_id]["messages"].append(event)

        # اگر تایمر قبلاً تنظیم نشده، یک تایمر ۱.۵ ثانیه تنظیم کن
        if not pending_albums[group_id]["timer"]:
            async def process_album_later(gid=group_id):
                await asyncio.sleep(1.5)  # کمی بیشتر از ربات برای اطمینان
                album = pending_albums.pop(gid, None)
                if not album:
                    return
                messages = album["messages"]
                # مرتب‌سازی بر اساس message_id
                messages.sort(key=lambda m: m.message.message_id)
                # فروارد همه به صورت پشت سر هم (بدون sleep)
                for e in messages:
                    try:
                        await client.forward_messages(BOT_USERNAME, e.message)
                        # بدون sleep عمدی؛ خود تلگرام آن‌ها را به‌عنوان یک گروه تحویل می‌دهد
                        await asyncio.sleep(0.05)  # یک تأخیر بسیار کوچک برای جلوگیری از رد شدن
                    except Exception as err:
                        print(f"⚠️ خطا در فروارد آلبوم: {err}")
                print(f"📸 آلبوم با {len(messages)} آیتم فروارد شد")
            pending_albums[group_id]["timer"] = asyncio.create_task(process_album_later())
    else:
        # پست تکی (غیر آلبوم) ← به صف اضافه شود
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
