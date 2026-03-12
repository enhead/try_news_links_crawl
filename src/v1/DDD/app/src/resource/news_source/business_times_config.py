"""
The Business Times 新闻源配置

新闻源信息：
- 网站：https://www.businesstimes.com.sg/
- 国家：新加坡 (SG)
- 语言：英语 (en)
- 爬取策略：枚举主要栏目 -> 不翻页（首页即可）

爬取层级结构：
  EnumerableLayer (category) - 枚举主要新闻栏目
    └─> SequentialLayer (page) - 每个栏目首页
          └─> CrawlNode - 执行HTTP请求和解析

栏目说明：
- singapore: 新加坡新闻（核心）
- international: 国际新闻
- companies-markets: 公司市场
- property: 房产
- startups-tech: 科技创业

URL结构：
- 栏目页：/category
- 分页：/category?page=2
- 文章页：/category/article-slug（一级）
- 文章页：/category/subcategory/article-slug（二级）

注意：
- 使用标准httpx即可
- URL包含跟踪参数 ?ref=xxx 需要清理
- 需要排除导航页、作者页、关键词页
"""

import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
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


@NewsSourceConfigRegistry.register("sg_business_times")
class BusinessTimesConfig(AbstractNewsSourceConfig):
    """The Business Times 新闻源配置实现"""

    def __init__(self, metadata: NewsSourceMetadata):
        """
        初始化 The Business Times 配置

        Args:
            metadata: 从数据库加载的新闻源元数据
        """
        # 爬取层级配置
        layer_schema = LayerSchema(
            type=LayerType.ENUMERABLE,
            key="category",
            values=[
                "singapore",           # 新加坡新闻
                "international",       # 国际新闻
                "companies-markets",   # 公司市场
                "property",            # 房产
                "startups-tech",       # 科技创业
                "opinion-features"     # 观点专题
            ],
            next=LayerSchema(
                type=LayerType.SEQUENTIAL,
                key="page",
                values=SequentialLayerConfig(
                    node_class=DefaultCrawlNode,
                    max_pages=1  # 只爬首页
                )
            )
        )

        # HTTP 请求模板配置
        request_template = RequestParameter(
            url="https://www.businesstimes.com.sg/{category}",
            method="GET",
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

    @staticmethod
    def _clean_url(url: str) -> str:
        """
        清理URL，移除跟踪参数

        Args:
            url: 原始URL

        Returns:
            清理后的URL
        """
        parsed = urlparse(url)

        # 解析查询参数
        query_params = parse_qs(parsed.query)

        # 移除跟踪参数
        tracking_params = ['ref', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content']
        cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}

        # 重新构建查询字符串
        if cleaned_params:
            query_string = urlencode(cleaned_params, doseq=True)
        else:
            query_string = ''

        # 重新构建URL
        cleaned_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            ''  # 移除fragment
        ))

        return cleaned_url

    def parse_response(self, response: Response) -> ResponseParseResultEntity:
        """
        解析 The Business Times 页面，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接
        3. 只保留 businesstimes.com.sg 域名的链接
        4. 自动补全相对路径为绝对路径
        5. 排除导航链接、分页链接、作者页、关键词页等
        6. 清理URL跟踪参数
        7. 去重

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
                    # 只保留 businesstimes.com.sg 域名
                    if 'businesstimes.com.sg' not in href:
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # 相对路径转为绝对路径
                    full_url = f"https://www.businesstimes.com.sg{href}"
                else:
                    continue

                # 排除非新闻页面
                exclude_patterns = [
                    '/breaking-news',
                    '/keywords/',
                    '/authors/',
                    '/tag/',
                    '/search',
                    '/newsletters',
                    '/content/',
                    '/help',
                    '/videos',
                    '/podcasts',
                    '/advertise',
                    '/events-awards',
                    '/paid-press-release',
                    '/thrive',
                    '/tech-in-asia',
                    '/zh-hans',
                    '/global',
                    'e-paper.sph.com.sg',
                    'subscribe.sph.com.sg',
                ]

                # 检查是否为排除模式
                if any(pattern in full_url for pattern in exclude_patterns):
                    continue

                # 排除栏目首页（精确匹配）
                if re.search(r'businesstimes\.com\.sg/(singapore|international|companies-markets|property|startups-tech|opinion-features|lifestyle|wealth|working-life|esg)$', full_url):
                    continue

                # 排除二级栏目首页
                if re.search(r'/(economy-policy|smes|banking-finance|reits-property|energy-commodities|telcos-media-tech|transport-logistics|consumer-healthcare|capital-markets-currencies|residential|commercial-industrial|asean|global)$', full_url):
                    continue

                # 新闻详情页格式匹配
                # 一级分类：/category/article-slug
                # 二级分类：/category/subcategory/article-slug
                article_pattern = r'businesstimes\.com\.sg/(singapore|international|companies-markets|property|startups-tech|opinion-features|lifestyle|wealth|working-life|esg)/[a-z0-9\-]+(/[a-z0-9\-]+)?$'

                if re.search(article_pattern, full_url):
                    # 清理URL参数
                    cleaned_url = self._clean_url(full_url)
                    urls.append(cleaned_url)

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
            "singapore": "新加坡 (Singapore)",
            "international": "国际 (International)",
            "companies-markets": "公司市场 (Companies & Markets)",
            "property": "房产 (Property)",
            "startups-tech": "科技创业 (Startups & Tech)",
            "opinion-features": "观点专题 (Opinion & Features)",
        }

        return category_map.get(category, category.title())
