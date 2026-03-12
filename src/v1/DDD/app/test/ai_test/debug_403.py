"""
Debug 403 问题 - 对比 curl 和 httpx 的请求差异
"""
import asyncio
import httpx

async def test():
    # 完全复制用户的成功配置
    headers = {
        "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
        "Accept": "*/*",
        "Host": "www.bharian.com.my",
        "Connection": "keep-alive"
    }

    test_cases = [
        ("Case1: User success URL", "https://www.bharian.com.my/berita/", None),
        ("Case2: No params", "https://www.bharian.com.my/berita/nasional", None),
        ("Case3: page=0", "https://www.bharian.com.my/berita/nasional", {"page": "0"}),
        ("Case4: page=1", "https://www.bharian.com.my/berita/nasional", {"page": "1"}),
    ]

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for name, url, params in test_cases:
            try:
                print(f"\n{'='*60}")
                print(f"Test: {name}")
                print(f"URL: {url}")
                if params:
                    print(f"Params: {params}")

                # Send request and print actual request info
                req = client.build_request("GET", url, params=params, headers=headers)
                print(f"Actual URL: {req.url}")
                print(f"Actual Headers: {dict(req.headers)}")

                resp = await client.send(req)
                print(f"[OK] Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  Content-Length: {len(resp.text)} bytes")

            except Exception as e:
                print(f"[ERROR] {e}")

asyncio.run(test())
