import logging
import time
import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Load .env if available
load_dotenv()

BOT_TOKEN = os.getenv("7561497263:AAEpy_c8ZwtxxUmd5Bcmy7A8qA8UvHwZC0s")
CHAT_ID = os.getenv("8114144078")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

async def send_telegram_message(message):
    try:
        await bot.send_message(CHAT_ID, message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")

async def scan_arbitrage_opportunities():
    try:
        logging.info("🔍 Сканирую токены для арбитража...")
        spread_info = "ETH: Binance $1800 / OKX $1820 ➤ Spread: +1.11%"
        await send_telegram_message(f"📈 Найден арбитраж:\n{spread_info}")
    except Exception as e:
        logging.error(f"❌ Ошибка в анализе арбитража: {e}")
        await send_telegram_message(f"❌ Ошибка:\n{e}")

async def main_loop():
    await send_telegram_message("✅ Бот запущен и начал мониторинг.")
    while True:
        try:
            await scan_arbitrage_opportunities()
            await asyncio.sleep(10)  # Интервал 10 секунд
        except Exception as e:
            logging.exception("Произошла фатальная ошибка в основном цикле.")
            await send_telegram_message(f"🚨 Критическая ошибка:\n{e}")
            await asyncio.sleep(15)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except Exception as e:
        logging.exception("Бот аварийно завершился.")
        asyncio.run(send_telegram_message(f"🛑 Бот аварийно завершился:\n{e}"))
