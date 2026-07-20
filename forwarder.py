import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# این مقادیر از Railway تزریق می‌شن
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
BOT_USERNAME = os.environ["BOT_USERNAME"]

# ========== کانال‌های مبدأ (ثابت) ==========
SOURCE_CHANNELS = [
    "@drtel",
    "@ChizNewz",
    "@khabarfuri",
    "@FieldReports",
]
# =========================================

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def forward_to_bot(event):
    await client.forward_messages(BOT_USERNAME, event.message)
    print(f"📤 فروارد شد از {event.chat.title}")

async def main():
    await client.start()
    print("🔥 یوزربات آماده است و این کانال‌ها را زیر نظر دارد:")
    for ch in SOURCE_CHANNELS:
        print(f"   ➜ {ch}")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
