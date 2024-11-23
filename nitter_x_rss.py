import feedparser
import telegram
import time
import json
from datetime import datetime
import os

# 설정 파일 로드
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# RSS 피드 파싱
def parse_rss_feed(feed_url):
    feed = feedparser.parse(feed_url)
    return feed.entries

# 텔레그램 메시지 전송
async def send_telegram_message(bot, chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

# 마지막 전송 시간 저장/로드
def save_last_time(timestamp):
    with open('last_check.txt', 'w') as f:
        f.write(str(timestamp))

def load_last_time():
    try:
        with open('last_check.txt', 'r') as f:
            return float(f.read().strip())
    except:
        return 0

async def main():
    config = load_config()
    bot = telegram.Bot(token=config['telegram_token'])
    last_check = load_last_time()

    while True:
        try:
            entries = parse_rss_feed(config['nitter_rss_url'])
            current_time = time.time()

            for entry in entries:
                entry_time = time.mktime(entry.published_parsed)
                if entry_time > last_check:
                    message = f"<b>{entry.title}</b>\n\n{entry.description}\n\n{entry.link}"
                    sent = await send_telegram_message(bot, config['telegram_chat_id'], message)
                    if sent:
                        save_last_time(current_time)
                        time.sleep(1)  # API 제한 방지

            time.sleep(config['check_interval'])

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
