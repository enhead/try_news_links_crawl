"""
测试 curl_cffi 是否能绕过 Cloudflare 403
需要先安装：pip install curl_cffi
"""

try:
    from curl_cffi import requests
    print("✓ curl_cffi 已安装")
except ImportError:
    print("✗ curl_cffi 未安装")
    print("请运行: pip install curl_cffi")
    exit(1)

# 测试配置
headers = {
    "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
    "Accept": "*/*",
    "Host": "www.bharian.com.my",
    "Connection": "keep-alive"
}

test_urls = [
    "https://www.bharian.com.my/berita/",
    "https://www.bharian.com.my/berita/nasional",
    "https://www.bharian.com.my/berita/nasional?page=0",
]

print("\n" + "="*60)
print("测试 curl_cffi (模拟真实 curl TLS 指纹)")
print("="*60)

for url in test_urls:
    print(f"\nURL: {url}")
    try:
        # impersonate="chrome" 会使用 Chrome 的 TLS 指纹
        # 也可以用 "chrome110", "safari15_5" 等
        resp = requests.get(
            url,
            headers=headers,
            impersonate="chrome120",  # 使用 Chrome 120 的 TLS 指纹
            timeout=10
        )

        status = resp.status_code
        print(f"  Status: {status}")

        if status == 200:
            print(f"  ✓ SUCCESS! Content length: {len(resp.text)} bytes")
            # 验证是否真的获取到了新闻列表
            if "berita" in resp.text.lower() or "nasional" in resp.text.lower():
                print(f"  ✓ 内容验证通过（包含新闻关键词）")
        elif status == 403:
            print(f"  ✗ FAILED! Still 403")
        else:
            print(f"  ? Unexpected status")

    except Exception as e:
        print(f"  ✗ ERROR: {type(e).__name__}: {e}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
