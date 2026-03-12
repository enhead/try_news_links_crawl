"""
BruDirect 新闻源配置

新闻源信息：
- 网站：https://brudirect.com/
- 国家：文莱 (BN)
- 语言：英语 (en)
- 爬取策略：枚举8个类别 -> 每个类别顺序翻页

爬取层级结构：
  EnumerableLayer (category) - 枚举8个主要类别
    └─> SequentialLayer (page) - 每个类别顺序翻页
          └─> CrawlNode - 执行HTTP请求和解析

类别说明：
- national-headline: 国内头条
- Press-Releases: 新闻发布
- world-headline: 国际头条
- world-sports: 世界体育
- science-technology: 科技
- entertainment: 娱乐
- xinhua-news-agency: 新华社
- features: 专题

分页规则：
- 列表页：/result.php?title=&category={category}&subcategory=&p={page}
- 每页约10条新闻
- 不同类别页数不同

注意：
- 使用标准httpx即可
- 新闻详情页格式多样：/post/{date-or-id}-{title-slug}
"""

import re
from bs4 import BeautifulSoup

from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.entity.response_parse_result_entity import ResponseParseResultEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj.response_parse_result_status_vo import ResponseParseResultStatusVO
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import AbstractNewsSourceConfig
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.registry.news_source_config_registry import NewsSourceConfigRegistry
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.crawl_node.impl.default_crawl_node import DefaultCrawlNode
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import LayerSchema, LayerType
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.impl.sequential_layer import SequentialLayerConfig
from v1.DDD.infrastructure.http.request_parameter import RequestParameter
from v1.DDD.infrastructure.http.response import Response


@NewsSourceConfigRegistry.register("bn_brudirect")
class BruDirectConfig(AbstractNewsSourceConfig):
    """BruDirect 新闻源配置实现"""

    def __init__(self, metadata: NewsSourceMetadata):
        """
        初始化 BruDirect 配置

        Args:
            metadata: 从数据库加载的新闻源元数据

        说明：
            该配置将在应用启动时由 NewsSourceConfigRegistry 自动加载。
            metadata 参数由 Registry 从数据库查询后传入，无需手动创建。
        """
        # 爬取层级配置
        layer_schema = LayerSchema(
            type=LayerType.ENUMERABLE,
            key="category",
            values=[
                "national-headline",      # 国内头条
                "Press-Releases",         # 新闻发布
                "world-headline",         # 国际头条
                "world-sports",           # 世界体育
                "science-technology",     # 科技
                "entertainment",          # 娱乐
                "xinhua-news-agency",     # 新华社
                "features"                # 专题
            ],
            next=LayerSchema(
                type=LayerType.SEQUENTIAL,
                key="page",
                values=SequentialLayerConfig(
                    node_class=DefaultCrawlNode,
                    start=1,                       # 第一页从1开始
                    step=1,
                    max_consecutive_empty=3,       # 连续3页无新链接则停止
                    max_consecutive_duplicate=3,   # 连续3页全是旧链接则停止
                    max_pages=10                   # 每个类别最多爬10页
                )
            )
        )

        # HTTP 请求模板配置
        request_template = RequestParameter(
            url="https://brudirect.com/result.php",
            method="GET",
            params={
                "title": "",
                "category": "{category}",  # category 占位符
                "subcategory": "",
                "p": "{page}"              # page 占位符
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
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
        解析 BruDirect 页面，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接（格式：/post/{various-formats}）
        3. 只保留 brudirect.com 域名的链接
        4. 自动补全相对路径为绝对路径
        5. 排除导航链接、作者链接等
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
                    # 只保留 brudirect.com 域名
                    if 'brudirect.com' not in href:
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # 相对路径转为绝对路径
                    full_url = f"https://brudirect.com{href}"
                else:
                    continue

                # 过滤规则：新闻详情页特征 /post/{anything}
                # 例如：
                # - /post/21/02/2026-Sistem-Pengangkutan-Darat,-SPD-Maintenance-Works
                # - /post/Business-Sentiment-Index-for-December-2025
                # - /post/guangdong-fifteen
                if not re.match(r'^https://brudirect\.com/post/.+', full_url):
                    continue

                # 排除非新闻页面
                exclude_patterns = [
                    '/author.php',
                    '/daywise.php',
                    '/tag.php',
                    '/result.php',
                    '/category.php',
                    '/search.php',
                ]
                if any(pattern in full_url for pattern in exclude_patterns):
                    continue

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

        将 URL 路径格式转换为可读的分类名称

        Args:
            params: 爬取参数，包含 category 字段

        Returns:
            格式化后的分类名称

        Examples:
            >>> extract_category({"category": "national-headline"})
            "国内头条 (National Headline)"

            >>> extract_category({"category": "world-sports"})
            "世界体育 (World Sports)"
        """
        category = params.get("category", "unknown")

        # 分类名称映射
        category_map = {
            "national-headline": "国内头条 (National Headline)",
            "Press-Releases": "新闻发布 (Press Releases)",
            "world-headline": "国际头条 (World Headline)",
            "world-sports": "世界体育 (World Sports)",
            "science-technology": "科技 (Science & Technology)",
            "entertainment": "娱乐 (Entertainment)",
            "xinhua-news-agency": "新华社 (Xinhua News Agency)",
            "features": "专题 (Features)",
        }

        return category_map.get(category, category.title())
