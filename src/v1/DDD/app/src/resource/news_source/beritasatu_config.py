"""
BeritaSatu.com 新闻源配置

新闻源信息：
- 网站：https://www.beritasatu.com/
- 国家：印度尼西亚 (ID)
- 语言：印度尼西亚语 (id)
- 爬取策略：枚举主要栏目 -> 不翻页（首页即可）

爬取层级结构：
  EnumerableLayer (category) - 枚举主要新闻栏目
    └─> SequentialLayer (page) - 每个栏目首页
          └─> CrawlNode - 执行HTTP请求和解析

栏目说明：
- nasional: 国内新闻（核心）
- nusantara: 地方/群岛新闻
- ekonomi: 经济新闻
- internasional: 国际新闻
- sport: 体育新闻
- lifestyle: 生活方式
- ototekno: 汽车科技

URL结构：
- 栏目页：/category
- 文章页：/category/article-id/article-slug（特殊：包含数字ID）

注意：
- 使用标准httpx即可
- URL格式特殊：包含数字ID，如 /nasional/2975467/article-title
- 需要排除导航页、标签页、作者页等
"""

import re
from urllib.parse import urlparse
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


@NewsSourceConfigRegistry.register("id_beritasatu")
class BeritaSatuConfig(AbstractNewsSourceConfig):
    """BeritaSatu.com 新闻源配置实现"""

    def __init__(self, metadata: NewsSourceMetadata):
        """
        初始化 BeritaSatu.com 配置

        Args:
            metadata: 从数据库加载的新闻源元数据
        """
        # 爬取层级配置
        layer_schema = LayerSchema(
            type=LayerType.ENUMERABLE,
            key="category",
            values=[
                "nasional",        # 国内新闻
                "nusantara",       # 地方/群岛
                "ekonomi",         # 经济
                "internasional",   # 国际
                "sport",           # 体育
                "lifestyle",       # 生活方式
                "ototekno",        # 汽车科技
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
            url="https://www.beritasatu.com/{category}",
            method="GET",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
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
        解析 BeritaSatu.com 页面，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接
        3. 只保留 beritasatu.com 域名的链接
        4. 自动补全相对路径为绝对路径
        5. 排除导航链接、标签页、作者页等
        6. 去重

        URL格式特点：
        - 文章页包含数字ID：/category/数字ID/article-slug
        - 例如：/nasional/2975467/article-title

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
                    # 只保留 beritasatu.com 域名
                    if 'beritasatu.com' not in href:
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # 相对路径转为绝对路径
                    full_url = f"https://www.beritasatu.com{href}"
                else:
                    continue

                # 排除非新闻页面
                exclude_patterns = [
                    '/tag/',                # 标签页
                    '/penulis/',            # 作者页
                    '/editor/',             # 编辑页
                    '/indeks',              # 索引页
                    '/bplus',               # B-Plus 内容
                    '/network',             # 网络页
                    '/beritasatu-live-streaming',  # 直播页
                    '/tentang-kami',        # 关于我们
                    '/redaksi',             # 编辑部
                    '/pedoman-media-siber', # 媒体准则
                    '/privacy-policy',      # 隐私政策
                    '/ketentuan-khusus',    # 特别条款
                    '/terpopuler',          # 热门索引
                    '/multimedia',          # 多媒体（避免视频、图片页）
                ]

                # 检查是否为排除模式
                if any(pattern in full_url for pattern in exclude_patterns):
                    continue

                # 排除栏目首页（精确匹配）
                if re.search(r'beritasatu\.com/(nasional|nusantara|ekonomi|internasional|sport|lifestyle|ototekno)$', full_url):
                    continue

                # 排除二级栏目首页
                # 如：/nasional/politik, /nasional/hukum-hankam, /ekonomi/makro
                if re.search(r'/(politik|hukum-hankam|kesra|religi|makro|bisnis|keuangan|industri|bola|raket|motor|otomotif|seleb|kuliner|travel|kesehatan)$', full_url):
                    continue

                # 新闻详情页格式匹配
                # 格式：/category/数字ID/article-slug
                # 例如：/nasional/2975467/muhammadiyah-tetapkan-idulfitri-1447-h-jatuh-pada-20-maret-2026
                article_pattern = r'beritasatu\.com/(nasional|nusantara|ekonomi|internasional|sport|lifestyle|ototekno|dki-jakarta|jabar|jateng|jatim|sumut|sumsel|bali|sulsel|kepri|banten)/\d+/[a-z0-9\-]+$'

                if re.search(article_pattern, full_url):
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
            "nasional": "国内 (Nasional)",
            "nusantara": "地方/群岛 (Nusantara)",
            "ekonomi": "经济 (Ekonomi)",
            "internasional": "国际 (Internasional)",
            "sport": "体育 (Sport)",
            "lifestyle": "生活方式 (Lifestyle)",
            "ototekno": "汽车科技 (Ototekno)",
        }

        return category_map.get(category, category.title())
