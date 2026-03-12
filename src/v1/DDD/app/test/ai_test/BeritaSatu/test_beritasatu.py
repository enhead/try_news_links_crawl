"""
BeritaSatu.com 配置测试脚本
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from v1.DDD.app.src.resource.news_source.beritasatu_config import BeritaSatuConfig
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.infrastructure.http.httpx_adapter import HttpxAdapter
from v1.DDD.infrastructure.http.request_parameter import RequestParameter

def test_beritasatu():
    """测试 BeritaSatu.com 配置"""

    print("=" * 60)
    print("BeritaSatu.com 配置测试")
    print("=" * 60)

    # 创建元数据
    metadata = NewsSourceMetadata(
        resource_id="id_beritasatu",
        name="BeritaSatu.com",
        domain="www.beritasatu.com",
        url="https://www.beritasatu.com",
        country="ID",
        language="id",
        status=0
    )

    # 创建配置实例
    config = BeritaSatuConfig(metadata)
    print(f"✓ 配置实例创建成功")

    # 测试解析
    print("\n1. 页面解析测试:")

    # 创建HTTP执行器
    executor = HttpxAdapter()

    # 测试抓取 nasional 栏目
    request = RequestParameter(
        url="https://www.beritasatu.com/nasional",
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )

    print(f"  正在抓取: {request.url}")
    response = executor.send(request)

    if response.success:
        print(f"  ✓ HTTP请求成功: status={response.status_code}")

        # 解析响应
        parse_result = config.parse_response(response)

        if parse_result.status.value == "SUCCESS":
            print(f"  ✓ 解析成功")
            print(f"  ✓ 发现链接数: {len(parse_result.urls)}")

            if parse_result.urls:
                print(f"\n  前10个链接示例:")
                for i, url in enumerate(parse_result.urls[:10], 1):
                    print(f"    {i}. {url}")

            # 验证URL格式
            print(f"\n  URL格式验证:")
            import re
            valid_count = 0
            pattern = r'/\d+/'  # 检查是否包含数字ID
            for url in parse_result.urls:
                if re.search(pattern, url) and 'beritasatu.com' in url:
                    valid_count += 1

            print(f"    有效URL数（包含数字ID）: {valid_count}/{len(parse_result.urls)}")
            print(f"    验证通过: {'✓' if valid_count == len(parse_result.urls) else '✗'}")

            # URL格式示例
            if parse_result.urls:
                print(f"\n  URL格式分析（第一个链接）:")
                first_url = parse_result.urls[0]
                print(f"    完整URL: {first_url}")
                parts = first_url.split('/')
                if len(parts) >= 5:
                    print(f"    栏目: {parts[3]}")
                    print(f"    文章ID: {parts[4]}")
                    print(f"    标题: {parts[5] if len(parts) > 5 else '无'}")

        else:
            print(f"  ✗ 解析失败: {parse_result.errors}")
    else:
        print(f"  ✗ HTTP请求失败: {response.error}")

    # 关闭HTTP客户端
    executor.close()

    # 测试分类提取
    print("\n2. 分类提取测试:")
    categories = ["nasional", "nusantara", "ekonomi", "internasional", "sport", "lifestyle", "ototekno"]
    for cat in categories:
        display_name = config.extract_category({"category": cat})
        print(f"  {cat} -> {display_name}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_beritasatu()
