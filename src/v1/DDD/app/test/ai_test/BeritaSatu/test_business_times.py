"""
The Business Times 配置测试脚本
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from v1.DDD.app.src.resource.news_source.business_times_config import BusinessTimesConfig
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.infrastructure.http.httpx_request_executor import HttpxRequestExecutor
from v1.DDD.infrastructure.http.request_parameter import RequestParameter

def test_business_times():
    """测试 The Business Times 配置"""

    print("=" * 60)
    print("The Business Times 配置测试")
    print("=" * 60)

    # 创建元数据
    metadata = NewsSourceMetadata(
        resource_id="sg_business_times",
        name="The Business Times",
        domain="www.businesstimes.com.sg",
        url="https://www.businesstimes.com.sg",
        country="SG",
        language="en",
        status=0
    )

    # 创建配置实例
    config = BusinessTimesConfig(metadata)
    print(f"✓ 配置实例创建成功")

    # 测试URL清理
    test_urls = [
        "https://www.businesstimes.com.sg/singapore/article-test?ref=home",
        "https://www.businesstimes.com.sg/property/real-estate?ref=footer&utm_source=test",
    ]

    print("\n1. URL清理测试:")
    for url in test_urls:
        cleaned = config._clean_url(url)
        print(f"  原始: {url}")
        print(f"  清理: {cleaned}\n")

    # 测试解析
    print("2. 页面解析测试:")

    # 创建HTTP执行器
    executor = HttpxRequestExecutor()

    # 测试抓取singapore栏目
    request = RequestParameter(
        url="https://www.businesstimes.com.sg/singapore",
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )

    print(f"  正在抓取: {request.url}")
    response = executor.execute(request)

    if response.success:
        print(f"  ✓ HTTP请求成功: status={response.status_code}")

        # 解析响应
        parse_result = config.parse_response(response)

        if parse_result.status.value == "SUCCESS":
            print(f"  ✓ 解析成功")
            print(f"  ✓ 发现链接数: {len(parse_result.urls)}")

            if parse_result.urls:
                print(f"\n  前5个链接示例:")
                for i, url in enumerate(parse_result.urls[:5], 1):
                    print(f"    {i}. {url}")

            # 验证URL格式
            print(f"\n  URL格式验证:")
            valid_count = 0
            for url in parse_result.urls:
                if 'businesstimes.com.sg' in url and '?ref=' not in url:
                    valid_count += 1
            print(f"    有效URL数: {valid_count}/{len(parse_result.urls)}")
            print(f"    验证通过: {'✓' if valid_count == len(parse_result.urls) else '✗'}")

        else:
            print(f"  ✗ 解析失败: {parse_result.errors}")
    else:
        print(f"  ✗ HTTP请求失败: {response.error}")

    # 关闭HTTP客户端
    executor.close()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_business_times()
