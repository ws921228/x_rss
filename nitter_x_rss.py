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

# 텔레그램 메시지 전송 함수 수정
async def send_telegram_message(bot, config, message):
    try:
        # 채널에 메시지 전송
        await bot.send_message(
            chat_id=config['telegram_channel_id'],
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=False
        )
        return True
    except Exception as e:
        print(f"Error sending message to channel: {e}")
        return False

# 마지막 전송 시간 저장/로드 함수를 GitHub 환경에 맞게 수정
def save_last_time(feed_name, timestamp):
    try:
        if not os.path.exists('.github/last_checks'):
            os.makedirs('.github/last_checks')
        with open(f'.github/last_checks/{feed_name}.txt', 'w') as f:
            f.write(str(timestamp))
    except Exception as e:
        print(f"Warning: Could not save timestamp: {e}")

def load_last_time(feed_name):
    try:
        with open(f'.github/last_checks/{feed_name}.txt', 'r') as f:
            return float(f.read().strip())
    except:
        # GitHub Actions에서 처음 실행시 현재 시간 - 1시간으로 설정
        return time.time() - 3600

async def process_feed(bot, config, feed_info):
    feed_name = feed_info['name']
    feed_url = feed_info['url']
    last_check = load_last_time(feed_name)
    current_time = time.time()

    try:
        entries = parse_rss_feed(feed_url)
        
        for entry in reversed(entries):
            entry_time = time.mktime(entry.published_parsed)
            if entry_time > last_check:
                message = (
                    f"🔔 새로운 포스트 - {feed_name}\n\n"
                    f"<b>{entry.title}</b>\n\n"
                    f"{entry.description}\n\n"
                    f"🔗 <a href='{entry.link}'>원본 링크</a>"
                )
                
                sent = await send_telegram_message(bot, config, message)
                if sent:
                    save_last_time(feed_name, current_time)
                    time.sleep(2)
    except Exception as e:
        print(f"Error processing feed {feed_name}: {e}")

async def main():
    try:
        config = load_config()
        bot = telegram.Bot(token=config['telegram_token'])
        
        # GitHub Actions에서는 한 번만 실행
        for feed in config['rss_feeds']:
            await process_feed(bot, config, feed)
            
    except Exception as e:
        print(f"Critical error: {e}")
        raise e  # GitHub Actions에서 오류 확인을 위해 예외 전파

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
