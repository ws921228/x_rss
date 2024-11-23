import feedparser
import telegram
import time
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
import os
import re
from datetime import timezone, timedelta

# KST 시간대 설정
KST = timezone(timedelta(hours=9))

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

def clean_html(raw_html):
    """HTML 태그를 텍스트로 변환하고 정리"""
    # HTML 태그 제거
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', raw_html)
    # 연속된 공백 제거
    text = ' '.join(text.split())
    # 특수 문자 이스케이프
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    return text

async def process_feed(bot, config, feed_info):
    feed_name = feed_info['name']
    feed_urls = feed_info['urls']  # 변경: url -> urls
    last_check = load_last_time(feed_name)
    current_time = time.time()

    for feed_url in feed_urls:  # 각 URL 시도
        try:
            entries = parse_rss_feed(feed_url)
            if entries:  # 성공적으로 피드를 가져온 경우
                print(f"Successfully fetched feed from: {feed_url}")
                
                for entry in reversed(entries):
                    # RSS의 pubDate 문자열을 datetime 객체로 변환
                    try:
                        if hasattr(entry, 'published'):
                            entry_date = parsedate_to_datetime(entry.published)
                        else:
                            entry_date = parsedate_to_datetime(entry.pubDate)
                        entry_time = entry_date.timestamp()
                    except Exception as e:
                        print(f"Error parsing date: {e}")
                        continue

                    if entry_time > last_check:
                        # description에서 HTML 태그 제거
                        clean_description = clean_html(entry.description)
                        
                        # UTC 시간을 KST로 변환
                        kst_time = entry_date.astimezone(KST)
                        
                        message = (
                            f"🔔 새로운 포스트 - {feed_name}\n\n"
                            f"<b>{clean_html(entry.title)}</b>\n\n"
                            f"{clean_description}\n\n"
                            f"🕐 {kst_time.strftime('%Y-%m-%d %H:%M:%S')} (KST)\n"
                            f"🔗 <a href='{entry.link}'>원본 링크</a>"
                        )
                        
                        sent = await send_telegram_message(bot, config, message)
                        if sent:
                            save_last_time(feed_name, current_time)
                            time.sleep(2)
                
                break  # 성공적으로 처리된 경우 다음 URL 시도하지 않음
                
        except Exception as e:
            print(f"Error with URL {feed_url}: {e}")
            continue  # 다음 URL 시도
    else:  # 모든 URL이 실패한 경우
        print(f"All URLs failed for feed {feed_name}")

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
