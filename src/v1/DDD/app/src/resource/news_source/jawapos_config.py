"""
JawaPos 新闻源配置

新闻源信息：
- 网站：https://www.jawapos.com/
- 国家：印度尼西亚 (ID)
- 语言：印度尼西亚语 (id)
- 爬取策略：枚举多个类别 -> 每个类别顺序翻页

爬取层级结构：
  EnumerableLayer (category) - 枚举4个类别
    └─> SequentialLayer (page) - 每个类别顺序翻页
          └─> CrawlNode - 执行HTTP请求和解析

类别说明：
- kabinet-merah-putih: 内阁红白（政治）
- nasional: 国内新闻
- entertainment: 娱乐新闻
- surabaya-raya: 泗水地区新闻
"""

from bs4 import BeautifulSoup

from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.entity.response_parse_result_entity import ResponseParseResultEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj import NewsSourceStatusVO
from v1.DDD.domain.http_news_links_crawl.model.valobj.response_parse_result_status_vo import ResponseParseResultStatusVO
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import AbstractNewsSourceConfig
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.registry.news_source_config_registry import NewsSourceConfigRegistry
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.crawl_node.impl.default_crawl_node import DefaultCrawlNode
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import LayerSchema, LayerType
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.impl.sequential_layer import SequentialLayerConfig
from v1.DDD.infrastructure.http.request_parameter import RequestParameter
from v1.DDD.infrastructure.http.response import Response


@NewsSourceConfigRegistry.register("id_jawapos")
class JawaPosConfig(AbstractNewsSourceConfig):
    """JawaPos 新闻源配置实现"""

    def __init__(self):
        """
        初始化 JawaPos 配置

        该配置将在应用启动时由 NewsSourceConfigRegistry 自动加载。
        数据库中需要有对应的 resource_id="id_jawapos" 记录。
        """
        # 元数据配置
        metadata = NewsSourceMetadata(
            resource_id="id_jawapos",
            name="Jawa Pos",
            domain="www.jawapos.com",
            url="https://www.jawapos.com",
            country="ID",
            language="id",
            status=NewsSourceStatusVO.NORMAL
        )

        # 爬取层级配置
        layer_schema = LayerSchema(
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
                    max_consecutive_empty=1,      # 连续1页无新链接则停止
                    max_consecutive_duplicate=1,  # 连续1页全是旧链接则停止
                    max_pages=5                    # 每个类别最多爬5页
                )
            )
        )

        # HTTP 请求模板配置
        request_template = RequestParameter(
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

        super().__init__(
            metadata=metadata,
            layer_schema=layer_schema,
            template_request_config=request_template
        )

    def parse_response(self, response: Response) -> ResponseParseResultEntity:
        """
        解析 JawaPos 页面，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接（至少3层路径）
        3. 只保留 www.jawapos.com 域名的链接（排除子域名）
        4. 自动补全相对路径为绝对路径
        5. 去重

        Args:
            response: HTTP 响应对象

        Returns:
            解析结果实体，包含提取的链接列表和错误信息
        """
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            errors = []

            # 查找所有新闻链接
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href', '')

                # 过滤规则：至少3层路径（/category/subcategory/article-title）
                if href.count('/') >= 3:
                    # 确保是完整 URL
                    if href.startswith('http'):
                        # 只保留 www.jawapos.com 域名的链接（排除子域名）
                        if href.startswith('https://www.jawapos.com/'):
                            urls.append(href)
                    elif href.startswith('/'):
                        # 相对路径转为绝对路径
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
        """
        从参数中提取分类

        将 URL 路径格式（kabinet-merah-putih）转换为标题格式（Kabinet Merah Putih）

        Args:
            params: 爬取参数，包含 category 字段

        Returns:
            格式化后的分类名称

        Examples:
            >>> extract_category({"category": "kabinet-merah-putih"})
            "Kabinet Merah Putih"

            >>> extract_category({"category": "entertainment"})
            "Entertainment"
        """
        category = params.get("category", "unknown")
        # 将短横线转为空格，并转换为标题格式
        return category.replace('-', ' ').title()
