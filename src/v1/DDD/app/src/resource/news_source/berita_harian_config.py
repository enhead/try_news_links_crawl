"""
Berita Harian 新闻源配置

新闻源信息：
- 网站：https://www.bharian.com.my/
- 国家：马来西亚 (MY)
- 语言：马来语 (ms)
- 爬取策略：枚举多个类别 -> 每个类别顺序翻页

爬取层级结构：
  EnumerableLayer (category) - 枚举9个主要类别
    └─> SequentialLayer (page) - 每个类别顺序翻页
          └─> CrawlNode - 执行HTTP请求和解析

类别说明：
- berita/nasional: 国内新闻
- berita/kes: 案件新闻
- berita/politik: 政治新闻
- berita/pendidikan: 教育新闻
- berita/wilayah: 地区新闻
- sukan: 体育新闻
- dunia: 世界新闻
- hiburan: 娱乐新闻
- bisnes: 商业新闻
"""

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


@NewsSourceConfigRegistry.register("my_berita_harian")
class BeritaHarianConfig(AbstractNewsSourceConfig):
    """Berita Harian 新闻源配置实现"""

    def __init__(self, metadata: NewsSourceMetadata):
        """
        初始化 Berita Harian 配置

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
                "berita/nasional",     # 国内新闻
                "berita/kes",          # 案件新闻
                "berita/politik",      # 政治新闻
                "berita/pendidikan",   # 教育新闻
                "berita/wilayah",      # 地区新闻
                "sukan",               # 体育
                "dunia",               # 世界
                "hiburan",             # 娱乐
                "bisnes"               # 商业
            ],
            next=LayerSchema(
                type=LayerType.SEQUENTIAL,
                key="page",
                values=SequentialLayerConfig(
                    node_class=DefaultCrawlNode,
                    start=0,                       # 第一页从0开始（?page=0 或不带参数）
                    step=1,
                    max_consecutive_empty=2,       # 连续2页无新链接则停止
                    max_consecutive_duplicate=2,   # 连续2页全是旧链接则停止
                    max_pages=5                    # 每个类别最多爬5页
                )
            )
        )

        # HTTP 请求模板配置（使用 Apifox User-Agent，已验证可用）
        request_template = RequestParameter(
            url="https://www.bharian.com.my/{category}",  # category 占位符
            method="GET",
            params={"page": "{page}"},  # page 占位符
            headers={
                "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
                "Accept": "*/*",
                "Host": "www.bharian.com.my",
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
        解析 Berita Harian 页面，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接（包含日期路径 /YYYY/MM/）
        3. 只保留 www.bharian.com.my 域名的链接
        4. 自动补全相对路径为绝对路径
        5. 排除特殊页面（/foto, /bhtv, /infografik 等）
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
                if not href or href.startswith('javascript:'):
                    continue

                # 处理完整 URL
                if href.startswith('http'):
                    # 只保留 www.bharian.com.my 域名
                    if not href.startswith('https://www.bharian.com.my/'):
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # 相对路径转为绝对路径
                    full_url = f"https://www.bharian.com.my{href}"
                else:
                    continue

                # 过滤规则：必须包含日期路径（新闻详情页特征）
                # 例如：/berita/kes/2026/03/1520108/...
                # 模式：至少包含 /YYYY/MM/
                import re
                if not re.search(r'/\d{4}/\d{2}/', full_url):
                    continue

                # 排除非新闻页面
                exclude_patterns = [
                    '/foto/',
                    '/bhtv/',
                    '/infografik/',
                    '/bhplus',
                    '/callback',
                    '/redaksi',
                    '/disclaimer',
                    '/data-peribadi',
                    '/iklanweb',
                    '/search',
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
            >>> extract_category({"category": "berita/nasional"})
            "Berita Nasional"

            >>> extract_category({"category": "sukan"})
            "Sukan"

            >>> extract_category({"category": "berita/kes"})
            "Berita Kes"
        """
        category = params.get("category", "unknown")

        # 分类名称映射（马来语 -> 中文说明）
        category_map = {
            "berita/nasional": "Berita Nasional",
            "berita/kes": "Berita Kes",
            "berita/politik": "Berita Politik",
            "berita/pendidikan": "Berita Pendidikan",
            "berita/wilayah": "Berita Wilayah",
            "sukan": "Sukan",
            "dunia": "Dunia",
            "hiburan": "Hiburan",
            "bisnes": "Bisnes",
        }

        return category_map.get(category, category.replace('/', ' ').title())
