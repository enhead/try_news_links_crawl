"""
BeritaSatu.com 网站分析脚本
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from v1.DDD.infrastructure.http.httpx_request_executor import HttpxRequestExecutor
from v1.DDD.infrastructure.http.request_parameter import RequestParameter
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

def analyze_beritasatu():
    """分析 BeritaSatu.com 网站结构"""

    print("=" * 80)
    print("BeritaSatu.com 网站分析")
    print("=" * 80)

    # 创建HTTP执行器
    executor = HttpxRequestExecutor()

    # 请求首页
    request = RequestParameter(
        url="https://www.beritasatu.com/",
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
    )

    print(f"\n1. 请求首页: {request.url}")
    response = executor.execute(request)

    if not response.success:
        print(f"   ✗ HTTP请求失败: {response.error}")
        print(f"   状态码: {response.status_code}")
        executor.close()
        return

    print(f"   ✓ HTTP请求成功: status={response.status_code}")
    print(f"   ✓ 内容长度: {len(response.text)} 字符")

    # 解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. 分析页面标题
    print(f"\n2. 页面标题:")
    title = soup.find('title')
    if title:
        print(f"   {title.text.strip()}")

    # 2. 查找所有链接
    print(f"\n3. 链接分析:")
    all_links = soup.find_all('a', href=True)
    print(f"   总链接数: {len(all_links)}")

    # 分类链接
    beritasatu_links = []
    category_links = []
    article_links = []

    for link in all_links:
        href = link.get('href', '')

        # 跳过空链接和JavaScript链接
        if not href or href.startswith('javascript:') or href.startswith('#'):
            continue

        # 处理完整URL
        if href.startswith('http'):
            if 'beritasatu.com' not in href:
                continue
            full_url = href
        elif href.startswith('/'):
            full_url = f"https://www.beritasatu.com{href}"
        else:
            continue

        beritasatu_links.append(full_url)

        # 分析URL结构
        parsed = urlparse(full_url)
        path_parts = [p for p in parsed.path.split('/') if p]

        # 可能的栏目链接（单层路径）
        if len(path_parts) == 1:
            category_links.append((full_url, path_parts[0]))
        # 可能的文章链接（多层路径）
        elif len(path_parts) >= 2:
            article_links.append(full_url)

    print(f"   BeritaSatu域名链接数: {len(beritasatu_links)}")
    print(f"   可能的栏目链接数: {len(category_links)}")
    print(f"   可能的文章链接数: {len(article_links)}")

    # 4. 分析可能的栏目
    print(f"\n4. 发现的可能栏目:")
    unique_categories = list(set([cat for _, cat in category_links]))
    for i, cat in enumerate(sorted(unique_categories)[:20], 1):
        print(f"   {i}. /{cat}")

    # 5. 分析文章链接格式
    print(f"\n5. 文章链接格式示例 (前10个):")
    for i, url in enumerate(article_links[:10], 1):
        parsed = urlparse(url)
        print(f"   {i}. {parsed.path}")

    # 6. 检查常见的新闻栏目关键词
    print(f"\n6. 常见新闻栏目检查:")
    common_categories = [
        'nasional', 'ekonomi', 'dunia', 'olahraga', 'hiburan',
        'teknologi', 'politik', 'bisnis', 'lifestyle', 'otomotif',
        'news', 'business', 'world', 'sports', 'entertainment'
    ]

    found_categories = []
    for cat in common_categories:
        if any(cat in link.lower() for link in beritasatu_links):
            found_categories.append(cat)

    if found_categories:
        print(f"   发现栏目: {', '.join(found_categories)}")
    else:
        print(f"   未发现常见栏目关键词")

    # 7. 检查是否有JavaScript渲染内容的迹象
    print(f"\n7. JavaScript检测:")
    script_tags = soup.find_all('script')
    print(f"   <script> 标签数: {len(script_tags)}")

    # 检查是否有React/Vue/Angular等框架
    page_text = response.text.lower()
    frameworks = {
        'react': 'react' in page_text,
        'vue': 'vue' in page_text or 'vuejs' in page_text,
        'angular': 'angular' in page_text or 'ng-app' in page_text,
        'next.js': 'next' in page_text and '__next' in page_text,
        'nuxt': 'nuxt' in page_text
    }

    detected = [name for name, found in frameworks.items() if found]
    if detected:
        print(f"   检测到前端框架: {', '.join(detected)}")
    else:
        print(f"   未检测到主流前端框架（可能是传统HTML）")

    # 8. 检查反爬虫机制
    print(f"\n8. 反爬虫机制检测:")

    # 检查Cloudflare
    if 'cloudflare' in page_text:
        print(f"   ⚠ 检测到 Cloudflare")

    # 检查验证码
    if 'captcha' in page_text or 'recaptcha' in page_text:
        print(f"   ⚠ 检测到验证码机制")

    # 检查robots.txt提示
    if 'robot' in page_text.lower():
        print(f"   检测到 robots 相关内容")

    # 9. 保存首页HTML（用于进一步分析）
    print(f"\n9. 保存HTML内容:")
    with open('beritasatu_homepage.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"   ✓ 已保存到: beritasatu_homepage.html")

    # 10. 生成分析报告
    report = {
        "url": "https://www.beritasatu.com/",
        "status": "success" if response.success else "failed",
        "http_status": response.status_code,
        "total_links": len(beritasatu_links),
        "category_count": len(unique_categories),
        "article_count": len(article_links),
        "found_categories": found_categories,
        "detected_frameworks": detected,
        "has_cloudflare": 'cloudflare' in page_text,
        "has_captcha": 'captcha' in page_text or 'recaptcha' in page_text
    }

    print(f"\n10. 分析报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 关闭HTTP客户端
    executor.close()

    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)

if __name__ == "__main__":
    analyze_beritasatu()
