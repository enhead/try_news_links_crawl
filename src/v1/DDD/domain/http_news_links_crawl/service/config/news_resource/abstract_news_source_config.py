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
from v1.DDD.infrastructure.http.request_parameter import RequestParameter

if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import LayerSchema
    from v1.DDD.infrastructure.http.response import Response


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


    # 原本想给健康检查用的但是发现其实用处不大
    def build_health_check_params_list(self) -> list[dict[str, Any]]:
        """
        构建健康检查参数列表（支持参数化配置）

        策略：
        1. 如果层有 `health_check` 字段，按字段指示执行：
           - "all": 遍历该层所有值
           - "first": 只取该层第一个值
        2. 如果没有 `health_check` 字段，使用默认策略：
           - 第一个枚举层：遍历所有值（相当于 "all"）
           - 其他枚举层：只取第一个值（相当于 "first"）
           - 顺序层：只取起始值（相当于 "first"）

        支持多层遍历，自动生成笛卡尔积。

        Returns:
            参数字典列表，每个字典对应一次健康检查请求

        Examples:
            >>> # 单枚举层（默认策略：遍历所有值）
            >>> layer_schema = [
            ...     {"type": "enumerable", "param_name": "category",
            ...      "values": ["politics", "tech", "sports"]},
            ...     {"type": "sequential", "param_name": "page", "start": 1}
            ... ]
            >>> config.build_health_check_params_list()
            [
                {"category": "politics", "page": 1},
                {"category": "tech", "page": 1},
                {"category": "sports", "page": 1}
            ]

            >>> # 多枚举层（第二层默认只取第一个）
            >>> layer_schema = [
            ...     {"type": "enumerable", "param_name": "cat1", "values": ["news", "blog"]},
            ...     {"type": "enumerable", "param_name": "cat2", "values": ["local", "world"]},
            ...     {"type": "sequential", "param_name": "page", "start": 1}
            ... ]
            >>> config.build_health_check_params_list()
            [
                {"cat1": "news", "cat2": "local", "page": 1},
                {"cat1": "blog", "cat2": "local", "page": 1}
            ]

            >>> # 显式配置多层遍历（笛卡尔积）
            >>> layer_schema = [
            ...     {"type": "enumerable", "param_name": "cat1", "values": ["a", "b"],
            ...      "health_check": "all"},
            ...     {"type": "enumerable", "param_name": "cat2", "values": ["x", "y"],
            ...      "health_check": "all"},
            ...     {"type": "sequential", "param_name": "page", "start": 1}
            ... ]
            >>> config.build_health_check_params_list()
            [
                {"cat1": "a", "cat2": "x", "page": 1},
                {"cat1": "a", "cat2": "y", "page": 1},
                {"cat1": "b", "cat2": "x", "page": 1},
                {"cat1": "b", "cat2": "y", "page": 1}
            ]
        """
        if not self.layer_schema:
            return [{}]

        # 查找需要遍历的层
        traverse_layers = self._find_traverse_layers()

        if not traverse_layers:
            # 如果没有需要遍历的层，返回单个默认参数
            return [self._build_default_params()]

        # 生成参数组合（笛卡尔积）
        return self._generate_params_combinations(traverse_layers)

    def _find_traverse_layers(self) -> list[dict]:
        """
        查找需要遍历的层

        根据 `health_check` 字段或默认策略确定哪些层需要遍历所有值。

        Returns:
            需要遍历的层列表
        """
        traverse_layers = []
        first_enum_found = False

        for layer in self.layer_schema:
            # 检查是否有显式配置
            health_check = layer.get("health_check")

            if health_check == "all":
                # 显式配置为遍历所有值
                traverse_layers.append(layer)

            elif health_check == "first":
                # 显式配置为只取第一个，跳过
                continue

            elif layer["type"] == "enumerable" and not first_enum_found:
                # 默认策略：第一个枚举层遍历所有值
                traverse_layers.append(layer)
                first_enum_found = True

        return traverse_layers

    def _generate_params_combinations(
        self, traverse_layers: list[dict]
    ) -> list[dict[str, Any]]:
        """
        生成参数组合（笛卡尔积）

        对需要遍历的层生成所有可能的组合，其他层使用默认值。

        Args:
            traverse_layers: 需要遍历的层列表

        Returns:
            参数字典列表
        """
        import itertools

        if not traverse_layers:
            return [self._build_default_params()]

        # 构建笛卡尔积的输入
        # 每个层的所有值：[["a", "b"], ["x", "y"]]
        layer_values = []
        layer_param_names = []

        for layer in traverse_layers:
            if layer["type"] == "enumerable":
                layer_values.append(layer["values"])
                layer_param_names.append(layer["param_name"])

        # 生成笛卡尔积
        # itertools.product(["a", "b"], ["x", "y"]) -> [("a", "x"), ("a", "y"), ("b", "x"), ("b", "y")]
        combinations = list(itertools.product(*layer_values))

        # 将笛卡尔积转换为参数字典列表
        result = []
        for combination in combinations:
            # 先构建默认参数（包含所有层的默认值）
            params = self._build_default_params()

            # 用遍历的值覆盖对应的参数
            for param_name, value in zip(layer_param_names, combination):
                params[param_name] = value

            result.append(params)

        return result

    def _build_default_params(self) -> dict[str, Any]:
        """
        为所有层构建默认参数（取第一个值/起始值）

        内部方法，用于生成非遍历层的默认参数。

        Returns:
            默认参数字典
        """
        params = {}

        for layer in self.layer_schema:
            param_name = layer["param_name"]

            if layer["type"] == "enumerable":
                # 枚举层：取第一个值（防御性检查）
                if layer.get("values"):
                    params[param_name] = layer["values"][0]

            elif layer["type"] == "sequential":
                # 顺序层：取起始值
                params[param_name] = layer["start"]

        return params

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