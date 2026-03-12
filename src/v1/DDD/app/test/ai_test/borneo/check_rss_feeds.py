"""
检查新闻网站是否提供 RSS Feed

策略：
1. 检查常见的 RSS URL 路径
2. 尝试从首页 HTML 中提取 RSS link 标签
3. 检查 sitemap.xml
"""

import asyncio
from curl_cffi.requests import AsyncSession
import re


TARGET_DOMAIN = "https://borneobulletin.com.bn"

# 常见的 RSS Feed 路径
COMMON_RSS_PATHS = [
    "/feed/",
    "/feed",
    "/rss/",
    "/rss",
    "/rss.xml",
    "/feed.xml",
    "/atom.xml",
    "/index.xml",
    "/feeds/",
    "/feeds/posts/default",  # Blogger 常用
    "/?feed=rss2",  # WordPress 常用
    "/wp-rss2.php",
]


async def check_url(session: AsyncSession, url: str) -> dict:
    """
    检查单个 URL 是否可访问

    Returns:
        dict: {"url": str, "status": int, "is_rss": bool, "title": str}
    """
    try:
        resp = await session.get(
            url,
            timeout=10,
            allow_redirects=True,
        )

        content = resp.text
        is_rss = any([
            "<?xml" in content[:100],
            "<rss" in content[:500],
            "<feed" in content[:500],
            "application/rss+xml" in content[:1000],
            "application/atom+xml" in content[:1000],
        ])

        # 尝试提取标题
        title = ""
        if is_rss:
            title_match = re.search(r"<title>([^<]+)</title>", content)
            if title_match:
                title = title_match.group(1)

        return {
            "url": url,
            "status": resp.status_code,
            "is_rss": is_rss,
            "title": title,
            "content_length": len(content),
        }

    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "error": str(e),
            "is_rss": False,
        }


async def extract_rss_from_homepage(session: AsyncSession, base_url: str) -> list[str]:
    """
    从首页 HTML 中提取 RSS link 标签

    查找类似：
    <link rel="alternate" type="application/rss+xml" href="/feed/" />
    """
    try:
        resp = await session.get(base_url, timeout=10)
        html = resp.text

        # 正则匹配 RSS link 标签
        rss_links = re.findall(
            r'<link[^>]*rel=["\']alternate["\'][^>]*type=["\']application/(?:rss|atom)\+xml["\'][^>]*href=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )

        # 也尝试反向匹配（type 在 rel 之前）
        rss_links += re.findall(
            r'<link[^>]*type=["\']application/(?:rss|atom)\+xml["\'][^>]*rel=["\']alternate["\'][^>]*href=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )

        return list(set(rss_links))

    except Exception as e:
        print(f"[ERROR] 提取 RSS 链接失败: {e}")
        return []


async def check_sitemap(session: AsyncSession, base_url: str) -> dict:
    """检查 sitemap.xml"""
    sitemap_url = f"{base_url}/sitemap.xml"
    try:
        resp = await session.get(sitemap_url, timeout=10)
        if resp.status_code == 200 and "<?xml" in resp.text[:100]:
            return {
                "url": sitemap_url,
                "status": 200,
                "has_sitemap": True,
            }
    except:
        pass

    return {"has_sitemap": False}


async def main():
    """主检查流程"""
    print("\n" + "="*60)
    print(f"检查 RSS Feed: {TARGET_DOMAIN}")
    print("="*60)

    session = AsyncSession(impersonate="chrome120")

    try:
        # 步骤1：从首页提取 RSS 链接
        print("\n[1/3] 从首页 HTML 提取 RSS 链接...")
        rss_links = await extract_rss_from_homepage(session, TARGET_DOMAIN)

        if rss_links:
            print(f"[SUCCESS] 找到 {len(rss_links)} 个 RSS 链接:")
            for link in rss_links:
                # 转换为完整 URL
                if link.startswith("http"):
                    full_url = link
                elif link.startswith("/"):
                    full_url = TARGET_DOMAIN + link
                else:
                    full_url = TARGET_DOMAIN + "/" + link
                print(f"  - {full_url}")

            # 验证这些链接
            print("\n验证提取的 RSS 链接...")
            for link in rss_links:
                if link.startswith("http"):
                    url = link
                elif link.startswith("/"):
                    url = TARGET_DOMAIN + link
                else:
                    url = TARGET_DOMAIN + "/" + link

                result = await check_url(session, url)
                if result["is_rss"]:
                    print(f"  [SUCCESS] {url}")
                    print(f"    标题: {result.get('title', 'N/A')}")
                else:
                    print(f"  [FAIL] {url} (状态: {result.get('status')})")
        else:
            print("[INFO] 未从首页提取到 RSS 链接")

        # 步骤2：尝试常见的 RSS 路径
        print("\n[2/3] 检查常见 RSS 路径...")
        found_feeds = []

        for path in COMMON_RSS_PATHS:
            url = TARGET_DOMAIN + path
            result = await check_url(session, url)

            if result["status"] == 200 and result["is_rss"]:
                print(f"  [SUCCESS] {url}")
                print(f"    标题: {result.get('title', 'N/A')}")
                found_feeds.append(url)
            elif result["status"] == 200:
                print(f"  [INFO] {url} - 可访问但不是 RSS ({result['content_length']} 字节)")
            # 不打印失败的，避免刷屏

        if not found_feeds:
            print("  [INFO] 未找到常见路径的 RSS Feed")

        # 步骤3：检查 sitemap
        print("\n[3/3] 检查 Sitemap...")
        sitemap = await check_sitemap(session, TARGET_DOMAIN)
        if sitemap["has_sitemap"]:
            print(f"  [SUCCESS] 找到 Sitemap: {sitemap['url']}")
        else:
            print("  [INFO] 未找到 Sitemap")

        # 总结
        print("\n" + "="*60)
        print("检查总结".center(60))
        print("="*60)

        all_feeds = list(set(found_feeds + [
            TARGET_DOMAIN + link if link.startswith("/") else link
            for link in rss_links
        ]))

        if all_feeds:
            print(f"\n[SUCCESS] 找到 {len(all_feeds)} 个可用的 RSS Feed:")
            for feed in all_feeds:
                print(f"  - {feed}")

            print("\n建议:")
            print("  1. 使用 RSS Feed 代替网页爬取")
            print("  2. 在新闻源配置中添加 RSS URL")
            print("  3. 实现 RSS 解析器（如使用 feedparser 库）")
        else:
            print("\n[FAIL] 未找到可用的 RSS Feed")
            print("\n该网站不提供 RSS 订阅，建议:")
            print("  1. 实现 PlaywrightAdapter 绕过 Cloudflare")
            print("  2. 或暂时跳过该新闻源")

        print("\n" + "="*60)

    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
