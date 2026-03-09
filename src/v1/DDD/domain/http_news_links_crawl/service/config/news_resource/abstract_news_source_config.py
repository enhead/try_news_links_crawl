"""
网络接口请求的新闻源配置抽象类

目标：
- 封装新闻源的元数据、爬虫配置和请求模板
- 提供请求构建和响应解析的抽象接口
- 支持从数据库或 JSON 配置加载
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any, TYPE_CHECKING

from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.entity.response_parse_result_entity import ResponseParseResultEntity
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.http.request_parameter import RequestParameter

if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.factory.layer_factory import LayerSchema
    from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.http.response import Response


class AbstractNewsSourceConfig(ABC):
    """
    新闻源配置抽象基类。

    封装新闻源的完整配置信息：
    - metadata: 新闻源元数据（来自数据库或配置文件）
    - layer_schema: 爬虫层级配置（枚举层、映射层、顺序层组合）
    - template_request_config: HTTP 请求模板（URL、参数、headers）

    子类需要实现：
    - parse_response(): 从响应中提取新闻链接
    - extract_category(): 从爬取参数中提取栏目分类
    """

    def __init__(
        self,
        metadata: NewsSourceMetadata,
        layer_schema: "LayerSchema",
        template_request_config: RequestParameter,
    ) -> None:
        """
        初始化新闻源配置。

        Args:
            metadata: 新闻源元数据（包含 resource_id, country, name, domain 等）
            layer_schema: 爬虫层级配置
            template_request_config: HTTP 请求模板
        """
        self.metadata = metadata
        self.layer_schema = layer_schema
        self.template_request_config = template_request_config

    # ------------------------------------------------------------------
    # 便捷属性：向后兼容，避免大量代码修改
    # ------------------------------------------------------------------

    @property
    def source_id(self) -> str:
        """新闻源唯一标识（向后兼容）"""
        return self.metadata.resource_id

    @property
    def country(self) -> str:
        """国家代码"""
        return self.metadata.country

    @property
    def name(self) -> str:
        """媒体机构名称"""
        return self.metadata.name

    @property
    def domain(self) -> str:
        """域名"""
        return self.metadata.domain

    @property
    def language(self) -> str:
        """语言代码"""
        return self.metadata.language

    # ------------------------------------------------------------------
    # 核心方法
    # ------------------------------------------------------------------

    def build_request(self, params: dict[str, Any]) -> RequestParameter:
        """
        将遍历参数填入 URL 模板和 query 参数，返回填充完毕的 RequestParameter。
        原始 template_request_config 保持不变，可复用。

        Args:
            params: 遍历参数，如 {"cat1": "tech", "cat2": "ai", "page": 1}

        Returns:
            填充后的 RequestParameter 对象
        """
        rc = self.template_request_config

        # 路径参数填充
        filled_url = rc.url.format(**params)

        # query 参数：值可以是占位符字符串，也可以是普通值
        filled_params = {
            k: v.format(**params) if isinstance(v, str) else v
            for k, v in rc.params.items()
        }

        # bearer token 注入到 headers
        headers = dict(rc.headers)
        if rc.bearer_token:
            headers["Authorization"] = f"Bearer {rc.bearer_token}"

        return replace(
            rc,
            url=filled_url,
            params=filled_params,
            headers=headers,
        )

    @abstractmethod
    def parse_response(self, response: "Response") -> ResponseParseResultEntity:
        """
        从响应中提取新闻链接。

        各新闻源页面结构差异大，子类必须自行实现。

        Args:
            response: HTTP 响应对象

        Returns:
            解析结果实体，包含提取的链接列表和错误信息
        """
        ...

    @abstractmethod
    def extract_category(self, params: dict[str, Any]) -> str:
        """
        从爬取参数中提取栏目分类。

        用于保存到数据库 news_link.category 字段。
        不同新闻源的参数结构不同，由子类根据实际情况实现。

        Args:
            params: 爬取参数，如 {"cat1": "tech", "cat2": "ai", "page": 1}

        Returns:
            栏目分类字符串，如 "Politics", "Technology"

        Examples:
            >>> # 示例1：单层分类
            >>> def extract_category(self, params):
            ...     return params.get("category", "Unknown")
            >>>
            >>> # 示例2：多层分类组合
            >>> def extract_category(self, params):
            ...     cat1 = params.get("cat1", "")
            ...     cat2 = params.get("cat2", "")
            ...     return f"{cat1}/{cat2}" if cat2 else cat1
        """
        ...