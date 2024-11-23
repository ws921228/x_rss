import telegram
import asyncio
import json

async def test_bot():
    # 설정 파일 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 봇 초기화
    bot = telegram.Bot(token=config['telegram_token'])
    
    # 봇 정보 출력
    bot_info = await bot.get_me()
    print(f"Bot Info: {bot_info.first_name} (@{bot_info.username})")
    
    # 테스트 메시지 전송
    try:
        # 개인 메시지 테스트
        await bot.send_message(
            chat_id=config['telegram_chat_id'],
            text="개인 메시지 테스트입니다."
        )
        print("개인 메시지 전송 성공")

        # 채널 메시지 테스트
        await bot.send_message(
            chat_id=config['telegram_channel_id'],
            text="채널 테스트 메시지입니다."
        )
        print("채널 메시지 전송 성공")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot())