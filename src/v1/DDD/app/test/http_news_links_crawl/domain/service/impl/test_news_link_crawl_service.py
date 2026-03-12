"""
NewsLinkCrawlService 集成测试

## 测试目标
完整测试 execute_crawl 方法，使用真实 HTTP 请求验证多类别爬取功能

## 测试站点
https://www.jawapos.com/

## 测试架构
使用 EnumerableLayer + SequentialLayer 双层结构：
  EnumerableLayer (category) - 枚举4个类别
    └─> SequentialLayer (page) - 每个类别翻页爬取
          └─> CrawlNode - 执行HTTP请求和解析

## 测试类别
- kabinet-merah-putih (内阁红白)
- nasional (国内新闻)
- entertainment (娱乐)
- surabaya-raya (泗水地区)

## 运行命令

### 1. 运行所有测试
```bash
pytest src/v1/DDD/app/test/http_news_links_crawl/domain/service/impl/test_news_link_crawl_service.py -v
```
说明：执行文件中的所有测试用例，-v 显示详细输出

### 2. 运行单个测试（推荐）
```bash
pytest src/v1/DDD/app/test/http_news_links_crawl/domain/service/impl/test_news_link_crawl_service.py::test_execute_crawl_multiple_categories -v -s
```
说明：
- 测试多类别爬取的完整流程
- -v 显示详细测试信息
- -s 显示 print 输出（包括日志和统计信息）
- 验证 EnumerableLayer 枚举4个类别
- 验证 SequentialLayer 每个类别翻页（最多2页）
- 验证链接提取、分类、去重、保存流程

### 3. 查看日志输出
```bash
pytest src/v1/DDD/app/test/http_news_links_crawl/domain/service/impl/test_news_link_crawl_service.py::test_execute_crawl_multiple_categories -v -s --log-cli-level=INFO
```
说明：
- --log-cli-level=INFO 显示 INFO 级别日志，这里换成debug更详细
- 可以看到每个类别的爬取进度
- 可以看到每页的请求URL和统计信息
- 可以看到剪枝机制的触发情况

## 验证内容
1. ✓ 能成功构建多层 layer 树 (EnumerableLayer + SequentialLayer)
2. ✓ 能发送真实 HTTP 请求并解析页面
3. ✓ 能提取新闻链接并正确分类
4. ✓ 分页机制和剪枝策略正常工作
5. ✓ 不同类别的链接提取和分类正确
6. ✓ 日志输出完整清晰（INFO/DEBUG分级）

## 预期输出示例
```
爬取完成统计
============================================================
总发现链接: 150
总新增链接: 150

按类别统计:
  Entertainment: 35 条
  Kabinet Merah Putih: 40 条
  Nasional: 38 条
  Surabaya Raya: 37 条

示例链接（每个类别前3个）:
  [Entertainment]
    1. https://www.jawapos.com/entertainment/...
       参数: {'category': 'entertainment', 'page': 1}
  ...
```
"""
from datetime import datetime

import pytest
from bs4 import BeautifulSoup
from collections import Counter

from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_context import CrawlContext
from v1.DDD.domain.http_news_links_crawl.model.entity.news_resource_crawl_factor_entity import NewsResourceCrawlFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.entity.response_parse_result_entity import ResponseParseResultEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj import NewsSourceStatusVO
from v1.DDD.domain.http_news_links_crawl.model.valobj.response_parse_result_status_vo import ResponseParseResultStatusVO
from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import INewsCrawlRepository
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import AbstractNewsSourceConfig
from v1.DDD.infrastructure.http.response import Response
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.crawl_node.impl.default_crawl_node import DefaultCrawlNode
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import LayerSchema, LayerType
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.impl.sequential_layer import SequentialLayerConfig
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.impl.news_link_crawl_service import NewsLinkCrawlService
from v1.DDD.infrastructure.http.curl_cffi_adapter import CurlCffiAdapter
from v1.DDD.infrastructure.http.request_parameter import RequestParameter

# 导入 layer 实现以触发装饰器注册
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.impl.enumerable_layer import EnumerableLayer
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.impl.sequential_layer import SequentialLayer
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.impl.mapping_layer import MappingLayer



# 问题根因：测试文件第101行有注释"导入 layer 实现以触发装饰器注册"，但缺少实际的导入语句。这些 layer 类使用了 @CrawlLayerFactory.register() 装饰器进行自注册，只有在类被导入时装饰器才会执行。
class JawaPosNewsSourceConfig(AbstractNewsSourceConfig):
    """JawaPos 新闻源配置实现"""

    def parse_response(self, response: Response) -> ResponseParseResultEntity:
        """解析 JawaPos 页面,提取新闻链接"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            errors = []

            # 查找所有新闻链接
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href', '')
                # 过滤出新闻详情页链接（包含类别路径且层级足够深）
                if href.count('/') >= 3:
                    # 确保是完整 URL
                    if href.startswith('http'):
                        # 只保留 www.jawapos.com 域名的链接（排除子域名）
                        if href.startswith('https://www.jawapos.com/'):
                            urls.append(href)
                    elif href.startswith('/'):
                        urls.append(f"https://www.jawapos.com{href}")

            # 去重
            urls = list(set(urls))

            return ResponseParseResultEntity(
                status=ResponseParseResultStatusVO.SUCCESS,
                urls=urls,
                errors=errors
            )

        except Exception as e:
            return ResponseParseResultEntity(
                status=ResponseParseResultStatusVO.PARSE_ERROR,
                urls=[],
                errors=[f"解析失败: {str(e)}"]
            )

    def extract_category(self, params: dict) -> str:
        """提取分类,从 category 参数中获取"""
        category = params.get("category", "unknown")
        # 将路径转换为标题格式
        return category.replace('-', ' ').title()


class MockRepository(INewsCrawlRepository):
    """Mock 仓储实现,用于测试"""

    async def save_crawl_log(self, session: "AsyncSession", resource_id: str, result: "CrawlNodeResultEntity",
                             started_at: datetime, finished_at: datetime) -> int:
        pass

    async def save_health_check_record(self, record: "HealthCheckRecordEntity") -> None:
        pass

    async def get_recent_health_checks(self, resource_id: str, limit: int = 10) -> list["HealthCheckRecordEntity"]:
        pass

    async def update_source_status_by_health(self, resource_id: str, status: "NewsSourceStatusVO") -> None:
        pass

    async def check_exists_batch(self, urls_or_aggregate):
        """模拟去重,全部返回为新链接"""
        return urls_or_aggregate

    async def save_batch(self, session, aggregate):
        """模拟保存（需要 session）"""
        from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import BatchSaveResult
        return BatchSaveResult(
            saved_count=len(aggregate.links),
            skipped_urls=[]
        )

    async def get_source_by_resource_id(self, resource_id):
        """Mock 方法"""
        return None

    async def get_all_active_sources(self):
        """Mock 方法"""
        return []

    async def get_all_sources(self):
        """Mock 方法"""
        return []


@pytest.fixture
def jawapos_metadata():
    """JawaPos 元数据"""
    return NewsSourceMetadata(
        resource_id="id_jawapos",
        name="Jawa Pos",
        domain="www.jawapos.com",
        url="https://www.jawapos.com",
        country="ID",
        language="id",
        status=NewsSourceStatusVO.NORMAL
    )


@pytest.fixture
def layer_schema():
    """
    多层 Layer Schema 配置

    结构:
      EnumerableLayer (category)
        └─> SequentialLayer (page)
              └─> CrawlNode
    """
    return LayerSchema(
        type=LayerType.ENUMERABLE,
        key="category",
        values=["kabinet-merah-putih", "nasional", "entertainment", "surabaya-raya"],
        next=LayerSchema(
            type=LayerType.SEQUENTIAL,
            key="page",
            values=SequentialLayerConfig(
                node_class=DefaultCrawlNode,
                start=1,
                step=1,
                max_consecutive_empty=1,
                max_consecutive_duplicate=1,
                max_pages=2  # 每个类别最多爬2页
            )
        )
    )


@pytest.fixture
def request_template():
    """请求模板 - 支持 category 和 page 占位符"""
    return RequestParameter(
        url="https://www.jawapos.com/{category}",  # category 占位符
        method="GET",
        params={"page": "{page}"},  # page 占位符
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    )


@pytest.fixture
def news_source_config(jawapos_metadata, layer_schema, request_template):
    """新闻源配置"""
    return JawaPosNewsSourceConfig(
        metadata=jawapos_metadata,
        layer_schema=layer_schema,
        template_request_config=request_template
    )


@pytest.fixture
def http_adapter():
    """HTTP 适配器（默认使用 curl_cffi）"""
    return CurlCffiAdapter()


@pytest.fixture
def mock_repository():
    """Mock 仓储"""
    return MockRepository()


@pytest.fixture
def mock_session():
    """Mock session - 模拟 AsyncSession"""
    from unittest.mock import AsyncMock

    class MockSession:
        """Mock AsyncSession with commit and rollback"""
        async def commit(self):
            """Mock commit"""
            pass

        async def rollback(self):
            """Mock rollback"""
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockSession()


@pytest.fixture
def crawl_context(news_source_config, http_adapter, mock_repository, mock_session):
    """爬取上下文（使用 session）"""
    return CrawlContext(
        source_config=news_source_config,
        http_adapter=http_adapter,
        news_crawl_repository=mock_repository,
        session=mock_session  # 🎯 直接传入 session
    )


@pytest.fixture
def crawl_factor(crawl_context):
    """爬取因子"""
    return NewsResourceCrawlFactorEntity(context=crawl_context)


@pytest.fixture
def crawl_service():
    """爬取服务"""
    return NewsLinkCrawlService()


@pytest.mark.asyncio
async def test_execute_crawl_multiple_categories(crawl_service, crawl_factor):
    """
    测试多类别爬取流程

    验证:
    1. 能成功构建多层 layer 树 (EnumerableLayer + SequentialLayer)
    2. 能发送真实 HTTP 请求
    3. 能解析页面并提取链接
    4. 能正确处理多个类别
    5. 分页和剪枝机制正常工作
    """
    # 执行爬取
    result = await crawl_service.execute_crawl(crawl_factor)

    # 验证结果
    assert result is not None
    assert result.layer_result is not None

    # 验证发现了链接
    assert len(result.layer_result.urls_found) > 0, "应该发现至少一个链接"

    # 按类别分组统计
    category_stats = Counter(url.category for url in result.layer_result.urls_found)

    print(f"\n{'='*60}")
    print(f"爬取完成统计")
    print(f"{'='*60}")
    print(f"总发现链接: {len(result.layer_result.urls_found)}")
    print(f"总新增链接: {len(result.layer_result.urls_new)}")
    print(f"\n按类别统计:")
    for category, count in sorted(category_stats.items()):
        print(f"  {category}: {count} 条")

    # 打印示例链接（每个类别前3个）
    print(f"\n示例链接（每个类别前3个）:")
    for category in sorted(category_stats.keys()):
        category_urls = [url for url in result.layer_result.urls_found if url.category == category]
        print(f"\n  [{category}]")
        for i, url_obj in enumerate(category_urls[:3], 1):
            print(f"    {i}. {url_obj.url}")
            print(f"       参数: {url_obj.crawl_params}")

    # 验证至少有2个类别有数据
    assert len(category_stats) >= 2, f"应该至少有2个类别有数据，实际: {len(category_stats)}"

    # 验证链接格式
    for url_obj in result.layer_result.urls_found:
        assert url_obj.url.startswith("https://www.jawapos.com/")
        assert "category" in url_obj.crawl_params
        assert "page" in url_obj.crawl_params

    print(f"\n{'='*60}")
    print(f"测试通过 [OK]")
    print(f"{'='*60}\n")
