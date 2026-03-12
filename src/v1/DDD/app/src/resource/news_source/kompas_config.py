"""
Kompas 新闻源配置

新闻源信息：
- 网站：https://www.kompas.com/
- 国家：印度尼西亚 (ID)
- 语言：印尼语 (id)
- 爬取策略：使用统一索引页 -> 顺序翻页

爬取层级结构：
  SequentialLayer (page) - 顺序翻页索引页
    └─> CrawlNode - 执行HTTP请求和解析

索引页说明：
- URL: https://indeks.kompas.com/
- 聚合所有30+个频道的最新新闻
- 分页：?page=1 到 ?page=15
- 每页约20条新闻，总计约300条最新新闻

新闻链接格式：
- https://{subdomain}.kompas.com/read/{YYYY}/{MM}/{DD}/{id}/{title-slug}
- 子域名包括：nasional, regional, megapolitan, money, bola, tekno, otomotif, etc.

注意：
- 使用标准httpx即可
- 索引页包含所有频道，无需单独爬取各子域名
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


@NewsSourceConfigRegistry.register("id_kompas")
class KompasConfig(AbstractNewsSourceConfig):
    """Kompas 新闻源配置实现"""

    def __init__(self, metadata: NewsSourceMetadata):
        """
        初始化 Kompas 配置

        Args:
            metadata: 从数据库加载的新闻源元数据

        说明：
            该配置将在应用启动时由 NewsSourceConfigRegistry 自动加载。
            metadata 参数由 Registry 从数据库查询后传入，无需手动创建。
        """
        # 爬取层级配置 - 使用单层顺序翻页
        layer_schema = LayerSchema(
            type=LayerType.SEQUENTIAL,
            key="page",
            values=SequentialLayerConfig(
                node_class=DefaultCrawlNode,
                start=1,                       # 第一页从1开始（不带参数或 ?page=1）
                step=1,
                max_consecutive_empty=3,       # 连续3页无新链接则停止
                max_consecutive_duplicate=3,   # 连续3页全是旧链接则停止
                max_pages=15                   # 索引页最多15页
            )
        )

        # HTTP 请求模板配置
        request_template = RequestParameter(
            url="https://indeks.kompas.com/",
            method="GET",
            params={"page": "{page}"},  # page 占位符
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "id,en-US;q=0.9,en;q=0.8",
                "Connection": "keep-alive"
            }
        )

        super().__init__(
            metadata=metadata,
            layer_schema=layer_schema,
            template_request_config=request_template
        )

    def build_request(self, params: dict) -> RequestParameter:
        """
        构建请求参数

        覆盖父类方法以处理第一页的特殊逻辑（第一页可以不带参数）

        Args:
            params: 爬取参数，包含 page

        Returns:
            构建好的请求参数
        """
        request = super().build_request(params)

        # 第一页可以不需要分页参数（但带上也可以）
        # 这里保持统一，都带上参数
        return request

    def parse_response(self, response: Response) -> ResponseParseResultEntity:
        """
        解析 Kompas 索引页，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接（格式：https://*.kompas.com/read/{YYYY}/{MM}/{DD}/{id}/{slug}）
        3. 只保留 kompas.com 域名的链接
        4. 自动补全相对路径为绝对路径
        5. 排除索引页、导航链接等
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
                    # 只保留 kompas.com 域名（包括所有子域名）
                    if '.kompas.com' not in href:
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # 相对路径 - 索引页的链接应该都是完整URL，这里做兼容处理
                    continue
                else:
                    continue

                # 过滤规则：新闻详情页特征
                # 格式：https://{subdomain}.kompas.com/read/{YYYY}/{MM}/{DD}/{id}/{slug}
                # 例如：https://nasional.kompas.com/read/2026/03/12/09595861/...
                if not re.match(
                    r'^https://[a-z]+\.kompas\.com/read/\d{4}/\d{2}/\d{2}/\d+/',
                    full_url
                ):
                    continue

                # 排除特殊页面
                exclude_patterns = [
                    '/advertorial/',
                    '/amp/',
                    'plus.kompas.com',
                    'account.kompas.com',
                    'activity.kompas.com',
                    'inside.kompas.com',
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

        由于使用索引页，这里返回"综合"

        Args:
            params: 爬取参数，包含 page 字段

        Returns:
            分类名称

        Examples:
            >>> extract_category({"page": 1})
            "Indeks - 综合"
        """
        page = params.get("page", 1)
        return f"Indeks - 综合 (第{page}页)"
