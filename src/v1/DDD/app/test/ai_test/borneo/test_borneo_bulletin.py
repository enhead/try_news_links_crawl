"""
测试 Borneo Bulletin 网站的可访问性

目标网站: https://borneobulletin.com.bn/
挑战: Cloudflare Bot Management 防护

测试策略:
1. 尝试不同的 impersonate 浏览器类型
2. 测试不同的 User-Agent 组合
3. 添加真实的浏览器 headers
"""

import asyncio
from curl_cffi.requests import AsyncSession


# 测试配置
TARGET_URL = "https://borneobulletin.com.bn/"

# 不同浏览器的 User-Agent
USER_AGENTS = {
    "chrome120": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "safari15_5": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
    "edge101": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53",
}

# 真实浏览器的 headers
BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ms;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    # 模拟从 Google 搜索过来
    "Referer": "https://www.google.com/",
}


async def test_single_impersonate(impersonate: str, use_custom_ua: bool = False):
    """
    测试单个 impersonate 配置

    Args:
        impersonate: 浏览器类型
        use_custom_ua: 是否使用自定义 User-Agent
    """
    print(f"\n{'='*60}")
    print(f"测试: {impersonate}")
    print(f"自定义 UA: {'是' if use_custom_ua else '否'}")
    print(f"{'='*60}")

    session = AsyncSession(impersonate=impersonate)

    try:
        # 构建 headers
        headers = BROWSER_HEADERS.copy()
        if use_custom_ua:
            headers["User-Agent"] = USER_AGENTS.get(impersonate, USER_AGENTS["chrome120"])

        # 发送请求
        resp = await session.get(
            TARGET_URL,
            headers=headers,
            timeout=30,
            allow_redirects=True,
        )

        # 分析结果
        status = resp.status_code
        content = resp.text
        content_length = len(content)

        print(f"状态码: {status}")
        print(f"内容长度: {content_length} 字节")

        # 检查是否是 Cloudflare 挑战页面
        is_cloudflare_challenge = any([
            "Cloudflare" in content,
            "请稍候" in content,
            "Just a moment" in content,
            "执行安全验证" in content,
            "Checking your browser" in content,
            "Ray ID" in content and content_length < 5000,
        ])

        if status == 200:
            if is_cloudflare_challenge:
                print("❌ 状态 200 但仍显示 Cloudflare 挑战页面")
                # 打印部分内容用于调试
                print("\n内容片段:")
                print(content[:500])
            else:
                print("✅ 成功绕过! 获取到真实内容")
                # 检查是否包含新闻内容
                if any(keyword in content.lower() for keyword in ["news", "article", "berita", "brunei"]):
                    print("✅ 内容验证通过 - 包含新闻关键词")
                return True
        elif status == 403:
            print(f"❌ 403 Forbidden - 被 Cloudflare 拦截")
        elif status == 503:
            print(f"❌ 503 Service Unavailable - 可能被限流")
        else:
            print(f"⚠️ 意外状态码: {status}")

        return False

    except Exception as e:
        print(f"❌ 请求失败: {type(e).__name__}: {e}")
        return False

    finally:
        await session.close()


async def test_all_combinations():
    """测试所有组合"""
    print("\n" + "🔍 开始测试 Borneo Bulletin 可访问性".center(60, "="))
    print(f"\n目标网站: {TARGET_URL}")
    print("\n测试策略:")
    print("  1. 不同的 impersonate 浏览器类型")
    print("  2. 默认 UA vs 自定义 UA")
    print("  3. 真实的浏览器 headers")

    impersonates = ["chrome120", "safari15_5", "edge101", "chrome110"]

    successful_configs = []

    for impersonate in impersonates:
        # 测试 1: 使用默认 UA
        success = await test_single_impersonate(impersonate, use_custom_ua=False)
        if success:
            successful_configs.append(f"{impersonate} (默认UA)")
            break  # 找到成功的就停止

        # 等待一下避免被限流
        await asyncio.sleep(2)

        # 测试 2: 使用自定义 UA
        success = await test_single_impersonate(impersonate, use_custom_ua=True)
        if success:
            successful_configs.append(f"{impersonate} (自定义UA)")
            break  # 找到成功的就停止

        # 等待一下避免被限流
        await asyncio.sleep(2)

    # 输出总结
    print("\n" + "="*60)
    print("测试总结".center(60))
    print("="*60)

    if successful_configs:
        print("\n✅ 成功的配置:")
        for config in successful_configs:
            print(f"  - {config}")
        print("\n建议: 使用上述配置创建新闻源配置")
    else:
        print("\n❌ 所有配置都失败了")
        print("\n可能的原因:")
        print("  1. Cloudflare Bot Management 等级太高")
        print("  2. 需要 JavaScript 执行才能通过验证")
        print("  3. 需要使用代理 IP")
        print("\n建议:")
        print("  1. 考虑使用代理服务")
        print("  2. 寻找该媒体的 RSS Feed")
        print("  3. 尝试使用 Playwright 模拟真实浏览器")

    print("\n" + "="*60)


async def test_with_delay():
    """
    测试加入延迟的效果
    模拟真实用户浏览行为
    """
    print("\n" + "="*60)
    print("测试: 模拟真实用户行为 (带延迟)")
    print("="*60)

    session = AsyncSession(impersonate="safari15_5")

    try:
        # 首页
        print("\n步骤 1: 访问首页...")
        resp = await session.get(
            TARGET_URL,
            headers=BROWSER_HEADERS,
            timeout=30,
        )
        print(f"首页状态码: {resp.status_code}")

        # 等待 3-5 秒（模拟用户阅读）
        print("等待 3 秒（模拟用户阅读）...")
        await asyncio.sleep(3)

        # 再次访问（此时可能已通过验证）
        print("\n步骤 2: 再次访问首页...")
        resp = await session.get(
            TARGET_URL,
            headers={
                **BROWSER_HEADERS,
                "Referer": TARGET_URL,  # 改为从自己来
            },
            timeout=30,
        )
        print(f"第二次状态码: {resp.status_code}")

        if resp.status_code == 200 and "Cloudflare" not in resp.text:
            print("✅ 成功! 延迟策略有效")
            return True
        else:
            print("❌ 延迟策略无效")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

    finally:
        await session.close()


if __name__ == "__main__":
    print("\n🚀 Borneo Bulletin 爬取可行性测试")
    print("="*60)

    # 主测试
    asyncio.run(test_all_combinations())

    # 额外测试：延迟策略
    print("\n\n")
    asyncio.run(test_with_delay())

    print("\n✨ 测试完成!")
