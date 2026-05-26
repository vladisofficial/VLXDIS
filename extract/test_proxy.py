import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector

PROXIES = [
    "Вставь сюда прокси через запятую",
    "socks5://Логин:Пароль@Айпи:Порт",
]

async def test_one(proxy_url):
    try:
        connector = ProxyConnector.from_url(proxy_url)
        async with aiohttp.ClientSession(connector=connector) as s:
            async with s.get("https://api.telegram.org", timeout=aiohttp.ClientTimeout(total=10)) as r:
                print(f"OK: {proxy_url} -> {r.status}")
                return True
    except Exception as e:
        print(f"FAIL: {proxy_url} -> {type(e).__name__}: {e}")
        return False

async def main():
    print(f"Тест {len(PROXIES)} прокси...\n")
    ok = 0
    for p in PROXIES:
        if await test_one(p):
            ok += 1
    print(f"\nРабочих: {ok}/{len(PROXIES)}")

asyncio.run(main())