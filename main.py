import asyncio
import aiohttp
import ccxt.async_support as ccxt
import logging
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    SPREAD_THRESHOLD_PERCENT,
    CHECK_INTERVAL_SECONDS,
    SUPPORTED_DEX_NETWORKS,
)
from telegram import Bot
from dex import get_dex_price

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Создаем асинхронные объекты ccxt для каждой биржи
CEX_EXCHANGES = {
    "binance": ccxt.binance(),
    "bybit": ccxt.bybit(),
    "bitget": ccxt.bitget(),
    "gate": ccxt.gateio(),
    "okx": ccxt.okx(),
    "mexc": ccxt.mexc(),
    "huobi": ccxt.huobi(),
    "kucoin": ccxt.kucoin(),
}

# Для примера: топ токенов (можно расширить с CoinGecko)
# Формат: (symbol для CEX, адрес токена ETH, BSC, Polygon)
TOKENS = [
    {
        "symbol": "BTC/USDT",
        "contracts": {
            "ethereum": "0xbtc_contract_eth",
            "bsc": "0xbtc_contract_bsc",
            "polygon": "0xbtc_contract_polygon",
        },
    },
    {
        "symbol": "ETH/USDT",
        "contracts": {
            "ethereum": "0xeth_contract_eth",
            "bsc": "0xeth_contract_bsc",
            "polygon": "0xeth_contract_polygon",
        },
    },
    # Добавь сюда реальных 50 токенов с правильными адресами
]

async def fetch_cex_price(exchange, symbol):
    try:
        ticker = await exchange.fetch_ticker(symbol)
        return ticker["last"]
    except Exception as e:
        logging.warning(f"CEX {exchange.id} error for {symbol}: {e}")
        return None

async def fetch_all_cex_prices(symbol):
    tasks = []
    for ex in CEX_EXCHANGES.values():
        tasks.append(fetch_cex_price(ex, symbol))
    results = await asyncio.gather(*tasks)
    return {ex_id: price for ex_id, price in zip(CEX_EXCHANGES.keys(), results) if price}

async def fetch_all_dex_prices(session, token):
    """
    Получаем цены на DEX в разных сетях
    """
    prices = {}
    for network in SUPPORTED_DEX_NETWORKS:
        contract_address = token["contracts"].get(network)
        if not contract_address:
            continue
        # Используем USDT в сети для сравнения
        # Адреса USDT в разных сетях можно вынести в config, для простоты ставим placeholder
        usdt_addresses = {
            "ethereum": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "bsc": "0x55d398326f99059fF775485246999027B3197955",
            "polygon": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        }
        usdt_address = usdt_addresses.get(network)
        if not usdt_address:
            continue

        # Для 0x API нужно указать sellToken (контракт токена) и buyToken (USDT)
        # Продаем 1 токен в минимальных единицах — для простоты возьмем 1 * 10^decimals
        # Тут без decimals — просто 10**18 (часто стандарты ERC20)
        sell_amount = 10**18

        price = await get_dex_price(session, network, contract_address, usdt_address, sell_amount)
        if price:
            prices[network] = price
    return prices

def find_arbitrage(prices):
    """
    Ищем максимальный и минимальный курс и считаем спред
    """
    if len(prices) < 2:
        return None
    min_ex, min_price = min(prices.items(), key=lambda x: x[1])
    max_ex, max_price = max(prices.items(), key=lambda x: x[1])
    spread_percent = ((max_price - min_price) / min_price) * 100
    if spread_percent >= SPREAD_THRESHOLD_PERCENT:
        return {
            "buy_exchange": min_ex,
            "buy_price": min_price,
            "sell_exchange": max_ex,
            "sell_price": max_price,
            "spread": round(spread_percent, 2),
        }
    return None

async def send_alert(token_symbol, arb, contracts):
    message = (
        f"🔍 Arbitrage opportunity for {token_symbol}\n\n"
        f"💰 Buy on {arb['buy_exchange']}: ${arb['buy_price']:.6f}\n"
        f"💸 Sell on {arb['sell_exchange']}: ${arb['sell_price']:.6f}\n"
        f"📊 Spread: {arb['spread']}%\n"
        f"🔗 Contracts:\n"
    )
    for net, addr in contracts.items():
        explorer = {
            "ethereum": "https://etherscan.io/token/",
            "bsc": "https://bscscan.com/token/",
            "polygon": "https://polygonscan.com/token/",
        }.get(net, "")
        if explorer:
            message += f"{net.capitalize()}: {explorer}{addr}\n"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def monitor():
    async with aiohttp.ClientSession() as session:
        while True:
            for token in TOKENS:
                cex_prices = await fetch_all_cex_prices(token["symbol"])
                dex_prices = await fetch_all_dex_prices(session, token)
                combined_prices = {**cex_prices, **dex_prices}
                arb = find_arbitrage(combined_prices)
                if arb:
                    await send_alert(token["symbol"], arb, token["contracts"])
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

async def close_exchanges():
    for ex in CEX_EX

