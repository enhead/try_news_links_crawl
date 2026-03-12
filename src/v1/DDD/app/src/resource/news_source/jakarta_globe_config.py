"""
Jakarta Globe 新闻源配置

新闻源信息：
- 网站：https://jakartaglobe.id/
- 国家：印度尼西亚 (ID)
- 语言：英语 (en)
- 爬取策略：枚举主要栏目 -> 每个栏目顺序翻页

爬取层级结构：
  EnumerableLayer (category) - 枚举主要新闻栏目
    └─> SequentialLayer (page) - 每个栏目顺序翻页
          └─> CrawlNode - 执行HTTP请求和解析

栏目说明：
- news: 新闻
- business: 商业
- lifestyle: 生活方式
- opinion: 观点
- world: 国际

分页规则：
- 列表页：/category/page/{page}
- 详情页：通常包含日期或ID

注意：
- 使用标准httpx即可
"""

# TODO：翻页会报错

import re
from bs4 import BeautifulSoup

from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.entity.response_parse_result_entity import ResponseParseResultEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj.response_parse_result_status_vo import ResponseParseResultStatusVO
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import \
    AbstractNewsSourceConfig
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.registry.news_source_config_registry import \
    NewsSourceConfigRegistry
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.crawl_node.impl.default_crawl_node import \
    DefaultCrawlNode
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import \
    LayerSchema, LayerType
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.impl.sequential_layer import \
    SequentialLayerConfig
from v1.DDD.infrastructure.http.request_parameter import RequestParameter
from v1.DDD.infrastructure.http.response import Response


@NewsSourceConfigRegistry.register("id_jakarta_globe")
class JakartaGlobeConfig(AbstractNewsSourceConfig):
    """Jakarta Globe 新闻源配置实现"""

    def __init__(self, metadata: NewsSourceMetadata):
        """
        初始化 Jakarta Globe 配置

        Args:
            metadata: 从数据库加载的新闻源元数据
        """
        # 爬取层级配置
        layer_schema = LayerSchema(
            type=LayerType.ENUMERABLE,
            key="category",
            values=[
                "news",  # 新闻
                "business",  # 商业
                "lifestyle",  # 生活方式
                "opinion",  # 观点
                "world"  # 国际
            ],
            next=LayerSchema(
                type=LayerType.SEQUENTIAL,
                key="page", # 这个 key 不会出现在 URL 里，但不影响
                values=SequentialLayerConfig(
                    node_class=DefaultCrawlNode,
                    max_pages=1
                )
            )
        )

        # HTTP 请求模板配置
        request_template = RequestParameter(
            url="https://jakartaglobe.id/{category}/newsindex",
            method="GET",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Connection": "keep-alive"
            }
        )

        super().__init__(
            metadata=metadata,
            layer_schema=layer_schema,
            template_request_config=request_template
        )

    def parse_response(self, response: Response) -> ResponseParseResultEntity:
        """
        解析 Jakarta Globe 页面，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接
        3. 只保留 jakartaglobe.id 域名的链接
        4. 自动补全相对路径为绝对路径
        5. 排除导航链接、分页链接等
        6. 去重

        Args:
            response: HTTP 响应对象

        Returns:
            解析结果实体，包含提取的链接列表和错误信息
        """
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            errors = []

            # 查找所有链接
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href', '')

                # 跳过空链接和 JavaScript 链接
                if not href or href.startswith('javascript:') or href.startswith('#'):
                    continue

                # 处理完整 URL
                if href.startswith('http'):
                    # 只保留 jakartaglobe.id 域名
                    if 'jakartaglobe.id' not in href:
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # 相对路径转为绝对路径
                    full_url = f"https://jakartaglobe.id{href}"
                else:
                    continue

                # 排除非新闻页面
                exclude_patterns = [
                    '/page/',
                    '/category/',
                    '/tag/',
                    '/author/',
                    '/search',
                    '/wp-content/',
                    '/feed/',
                    '/css/',
                    '/img/',
                    '/newsindex',
                ]

                # 检查是否为排除模式
                if any(pattern in full_url for pattern in exclude_patterns):
                    continue

                # 排除栏目首页（精确匹配）
                if re.search(r'jakartaglobe\.id/(news|business|lifestyle|opinion|world|tech)$', full_url):
                    continue

                # 新闻详情页格式：/category/article-slug
                # 匹配格式：以栏目名开头，后面跟着文章slug
                if re.search(r'/(news|business|lifestyle|opinion|world|tech)/[a-z0-9\-]+$', full_url):
                    urls.append(full_url)

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
        """
        从参数中提取分类

        Args:
            params: 爬取参数，包含 category 字段

        Returns:
            格式化后的分类名称
        """
        category = params.get("category", "unknown")

        # 分类名称映射
        category_map = {
            "news": "新闻 (News)",
            "business": "商业 (Business)",
            "lifestyle": "生活方式 (Lifestyle)",
            "opinion": "观点 (Opinion)",
            "world": "国际 (World)",
        }

        return category_map.get(category, category.title())
