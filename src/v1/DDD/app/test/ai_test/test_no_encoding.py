"""
Test with disabled auto-encoding and cookies
"""
import asyncio
import httpx

async def test():
    headers = {
        "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
        "Accept": "*/*",
        "Host": "www.bharian.com.my",
        "Connection": "keep-alive",
        "Accept-Encoding": "identity"  # Disable compression
    }

    # Disable cookies and auto-encoding
    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        default_encoding="utf-8"
    ) as client:
        url = "https://www.bharian.com.my/berita/"

        print("Testing with:")
        print(f"  URL: {url}")
        print(f"  Accept-Encoding: identity (disabled compression)")
        print(f"  Cookies: disabled")

        try:
            resp = await client.get(url, headers=headers)
            print(f"\nStatus: {resp.status_code}")
            if resp.status_code == 200:
                print(f"SUCCESS! Content length: {len(resp.text)}")
            else:
                print(f"FAILED! Headers sent: {resp.request.headers}")
        except Exception as e:
            print(f"ERROR: {e}")

asyncio.run(test())
