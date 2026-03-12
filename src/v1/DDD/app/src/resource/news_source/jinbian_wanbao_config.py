"""
金边晚报 新闻源配置

新闻源信息：
- 网站：http://www.jinbianwanbao.cn/
- 国家：柬埔寨 (KH)
- 语言：中文简体 (zh-CN)
- 爬取策略：枚举多个类别 -> 每个类别顺序翻页

爬取层级结构：
  EnumerableLayer (category) - 枚举5个主要类别
    └─> SequentialLayer (page) - 每个类别顺序翻页
          └─> CrawlNode - 执行HTTP请求和解析

类别说明：
- news: 时政要闻
- zhxw: 综合新闻
- product: 图片新闻
- case: 旅游天地
- job: 广告专栏

分页规则：
- 第一页：/{category}.html
- 第二页及以后：/{category}.html?pagesize=20&p={page}
- 每页20条新闻

注意：
- 使用标准httpx即可，无需特殊适配
- 新闻详情页格式：/{category}/{id}.html
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


@NewsSourceConfigRegistry.register("kh_jinbian_wanbao")
class JinbianWanbaoConfig(AbstractNewsSourceConfig):
    """金边晚报 新闻源配置实现"""

    def __init__(self, metadata: NewsSourceMetadata):
        """
        初始化金边晚报配置

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
                "news",      # 时政要闻
                "zhxw",      # 综合新闻
                "product",   # 图片新闻
                "case",      # 旅游天地
                "job"        # 广告专栏
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
                    max_pages=1                    # 每个类别最多爬10页
                )
            )
        )

        # HTTP 请求模板配置
        request_template = RequestParameter(
            url="http://www.jinbianwanbao.cn/{category}.html",  # category 占位符
            method="GET",
            params={
                "pagesize": "20",
                "p": "{page}"  # page 占位符
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
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

        覆盖父类方法以处理第一页的特殊逻辑（第一页不需要分页参数）

        Args:
            params: 爬取参数，包含 category 和 page

        Returns:
            构建好的请求参数
        """
        request = super().build_request(params)

        # 第一页不需要分页参数
        page = params.get("page", 1)
        if page == 1:
            request.params = {}

        return request

    def parse_response(self, response: Response) -> ResponseParseResultEntity:
        """
        解析金边晚报页面，提取新闻链接

        提取规则：
        1. 查找所有带 href 的 <a> 标签
        2. 过滤出新闻详情页链接（格式：/{category}/{id}.html）
        3. 只保留 jinbianwanbao.cn 域名的链接
        4. 自动补全相对路径为绝对路径
        5. 排除分页链接、导航链接等
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
                    # 只保留 jinbianwanbao.cn 域名
                    if 'jinbianwanbao.cn' not in href:
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # 相对路径转为绝对路径
                    full_url = f"http://www.jinbianwanbao.cn{href}"
                else:
                    continue

                # 过滤规则：新闻详情页特征 /{category}/{id}.html
                # 例如：/news/19237.html, /zhxw/19372.html
                if not re.match(r'^http://www\.jinbianwanbao\.cn/(news|zhxw|product|case|job)/\d+\.html$', full_url):
                    continue

                # 排除非新闻页面
                exclude_patterns = [
                    '/index.html',
                    '/aboutus.html',
                    '/contactus.html',
                    '/guestbook.html',
                    '/map.html',
                    '/annnouncement',
                    '/public/',
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
            >>> extract_category({"category": "news"})
            "时政要闻"

            >>> extract_category({"category": "zhxw"})
            "综合新闻"

            >>> extract_category({"category": "product"})
            "图片新闻"
        """
        category = params.get("category", "unknown")

        # 分类名称映射
        category_map = {
            "news": "时政要闻",
            "zhxw": "综合新闻",
            "product": "图片新闻",
            "case": "旅游天地",
            "job": "广告专栏",
        }

        return category_map.get(category, category.title())
