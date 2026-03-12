"""
使用 Playwright 成功的请求头测试 curl_cffi

策略：
1. 使用 Playwright 提取的完整请求头（包括 cf_clearance cookie）
2. 测试 curl_cffi 是否能使用这些请求头成功访问
3. 对比结果，分析差异

预期：
- 可能失败：cookie 与浏览器指纹绑定，无法跨会话复用
- 可能成功：如果只是请求头的问题
"""

import asyncio
from curl_cffi.requests import AsyncSession


TARGET_URL = "https://borneobulletin.com.bn/"

# Playwright 成功的完整请求头
PLAYWRIGHT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "max-age=0",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# Playwright 获取的 Cookie（关键：cf_clearance）
PLAYWRIGHT_COOKIES = "cf_clearance=LlAtQKA92c7lbckLJHTGnt348OohIfESXtYbWB7OnKY-1773287543-1.2.1.1-zH86wyM0GS.Ck5QtFeN.jC9m7oZ1t8L_O9FQ_ewi2tPHQbou5D_tCXFoY9r9jJd4RxnWuuhYWhqIoual5p.JzCnTYlHuSvAJJ5pzCbRLXqEGq7liUoC4Zqr.KU.1gHD3syjamPlmRtI9LrcPNMniOHWk5LEyy6p_AKAUU7dn6UuXGRT140FFCMIC_c2eivFujyi7gtoeyj_S5FAsAHjSBtZWCMKcEkiw7kZzKQPeaVwAwnUdCACnisTki1Qmeyou; _ga_NK2L6R3W5K=GS1.1.1773287542.1.1.1773287960.58.0.0"


async def test_with_playwright_headers():
    """
    测试1：使用完整的 Playwright 请求头（包括 cookie）
    """
    print("\n" + "="*60)
    print("测试1: 使用 Playwright 的完整请求头 + Cookie")
    print("="*60)

    session = AsyncSession(impersonate="chrome120")

    try:
        headers = PLAYWRIGHT_HEADERS.copy()
        headers["cookie"] = PLAYWRIGHT_COOKIES

        resp = await session.get(
            TARGET_URL,
            headers=headers,
            timeout=30,
            allow_redirects=True,
        )

        status = resp.status_code
        content = resp.text
        content_length = len(content)

        print(f"\n状态码: {status}")
        print(f"内容长度: {content_length} 字节")

        # 检查是否是 Cloudflare 挑战页面
        is_cloudflare = any([
            "Cloudflare" in content,
            "Just a moment" in content,
            "Checking your browser" in content,
            "Ray ID" in content and content_length < 5000,
        ])

        if status == 200:
            if is_cloudflare:
                print("[FAIL] 状态 200 但仍是 Cloudflare 挑战页面")
                print("\n可能原因:")
                print("  - cf_clearance cookie 已过期")
                print("  - cookie 与浏览器指纹绑定，无法跨会话使用")
                print("\n内容片段:")
                print(content[:500])
            else:
                print("[SUCCESS] 成功！使用 Playwright 的 cookie 绕过了 Cloudflare")
                if any(kw in content.lower() for kw in ["news", "article", "brunei"]):
                    print("[SUCCESS] 内容验证通过 - 包含新闻关键词")
                return True
        else:
            print(f"[FAIL] HTTP {status} - 请求失败")
            print("\n内容片段:")
            print(content[:500])

        return False

    except Exception as e:
        print(f"[ERROR] 请求异常: {type(e).__name__}: {e}")
        return False

    finally:
        await session.close()


async def test_without_cookie():
    """
    测试2：只使用 Playwright 的请求头，不带 cookie

    目的：验证是否是 cookie 起作用，还是请求头本身
    """
    print("\n" + "="*60)
    print("测试2: 只使用 Playwright 的请求头（不带 Cookie）")
    print("="*60)

    session = AsyncSession(impersonate="chrome120")

    try:
        resp = await session.get(
            TARGET_URL,
            headers=PLAYWRIGHT_HEADERS,
            timeout=30,
            allow_redirects=True,
        )

        status = resp.status_code
        content = resp.text
        content_length = len(content)

        print(f"\n状态码: {status}")
        print(f"内容长度: {content_length} 字节")

        is_cloudflare = any([
            "Cloudflare" in content,
            "Just a moment" in content,
            "Checking your browser" in content,
        ])

        if status == 200 and not is_cloudflare:
            print("[SUCCESS] 成功！只需要 Playwright 的请求头")
            return True
        else:
            print("[FAIL] 失败 - 需要 cf_clearance cookie 才能访问")
            return False

    except Exception as e:
        print(f"[ERROR] 请求异常: {type(e).__name__}: {e}")
        return False

    finally:
        await session.close()


async def test_with_safari_impersonate():
    """
    测试3：尝试使用 Safari 指纹 + Playwright 请求头

    目的：测试不同浏览器指纹的效果
    """
    print("\n" + "="*60)
    print("测试3: Safari 指纹 + Playwright Cookie")
    print("="*60)

    session = AsyncSession(impersonate="safari15_5")

    try:
        headers = PLAYWRIGHT_HEADERS.copy()
        headers["cookie"] = PLAYWRIGHT_COOKIES

        resp = await session.get(
            TARGET_URL,
            headers=headers,
            timeout=30,
            allow_redirects=True,
        )

        status = resp.status_code
        content_length = len(resp.text)

        print(f"\n状态码: {status}")
        print(f"内容长度: {content_length} 字节")

        is_cloudflare = "Cloudflare" in resp.text

        if status == 200 and not is_cloudflare:
            print("[SUCCESS] Safari 指纹成功")
            return True
        else:
            print("[FAIL] Safari 指纹也失败")
            return False

    except Exception as e:
        print(f"[ERROR] 请求异常: {type(e).__name__}: {e}")
        return False

    finally:
        await session.close()


async def main():
    """主测试流程"""
    print("\n" + "Borneo Bulletin - curl_cffi + Playwright Headers 测试".center(60, "="))
    print(f"\n目标: {TARGET_URL}")
    print("\n测试目的:")
    print("  验证能否将 Playwright 获取的 cookie 用于 curl_cffi")

    results = []

    # 测试1：完整的 Playwright 请求（含 cookie）
    success1 = await test_with_playwright_headers()
    results.append(("Playwright Headers + Cookie", success1))
    await asyncio.sleep(2)

    # 测试2：只用请求头，不带 cookie
    success2 = await test_without_cookie()
    results.append(("只用 Playwright Headers", success2))
    await asyncio.sleep(2)

    # 测试3：Safari 指纹 + cookie
    success3 = await test_with_safari_impersonate()
    results.append(("Safari + Playwright Cookie", success3))

    # 总结
    print("\n" + "="*60)
    print("测试总结".center(60))
    print("="*60)

    for test_name, success in results:
        status = "[SUCCESS]" if success else "[FAIL]"
        print(f"{test_name}: {status}")

    if not any(success for _, success in results):
        print("\n" + "="*60)
        print("结论".center(60))
        print("="*60)
        print("\n[FAIL] 所有测试都失败了")
        print("\n原因分析:")
        print("  1. cf_clearance cookie 与浏览器会话绑定")
        print("     - Cloudflare 会验证 cookie 的来源（IP、TLS 指纹、UA 等）")
        print("     - 跨会话复用 cookie 会被识别")
        print("\n  2. Cloudflare Bot Management 级别太高")
        print("     - 需要 JavaScript 执行才能获取有效 cookie")
        print("     - curl_cffi 无法执行 JavaScript")
        print("\n解决方案:")
        print("  [+] 方案1: 使用 Playwright 作为 HTTP 适配器")
        print("     - 创建 PlaywrightAdapter 继承 BaseHttpAdapter")
        print("     - 专门处理需要 JavaScript 的站点")
        print("\n  [+] 方案2: 寻找该媒体的 RSS Feed 或 API")
        print("     - 绕过网页爬取")
        print("\n  [-] 方案3: 代理服务")
        print("     - 成本高，不可靠")
    else:
        print("\n[SUCCESS] 找到可行方案！")
        successful = [name for name, success in results if success]
        print(f"\n成功的配置: {', '.join(successful)}")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
