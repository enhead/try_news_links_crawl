"""
网络接口请求的新闻源模板类

目标：
- 将用于提供新闻源请求所需的必要参数
- 对于能够使用网络接口请求仅用这个就能够全部配置出来


后面HTTP请求倾向于httpx依赖，但是为了后续拓展性，这里还是使用必要参数返回了具体看我自定义的RequestConfig，这里决定跟这个配合，然后使用的时候在做一次转接
"""

# TODO 还是差点，主要还有个问题，就是页面内容前需要先检查下，这里我还需要看看，目前计划在parse_response()中加

from abc import ABC, abstractmethod
from copy import replace  # Python 3.13+；3.12 以下用 dataclasses.replace
from dataclasses import replace, field, dataclass
from typing import Any, TYPE_CHECKING

from v1.DDD.domain.http_news_links_crawl.model.entity.response_parse_result_entity import ResponseParseResultEntity
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.http.request_parameter import RequestParameter

# TODO：下面还没有想好
if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.factory.layer_factory import LayerSchema
    from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.http.response import Response


class AbstractNewsSourceConfig(ABC):
    """
    新闻源配置抽象基类。

    - build_request  : 将遍历参数填入模板，返回填充完毕的 RequestParameter
    - parse_response : 子类必须实现，从响应中提取链接列表
    """

    def __init__(
        self,
        source_id: str,
        layer_schema: "LayerSchema",    # 爬虫配置
        template_request_config: RequestParameter,  # TODO：这里还涉及一些模板替换，感觉这个类其实还是设计下更好
    ) -> None:
        self.source_id = source_id
        self.layer_schema = layer_schema
        self.template_request_config = template_request_config

    # ------------------------------------------------------------------

    def build_request(self, params: dict[str, Any]) -> RequestParameter:
        """
        将遍历参数填入 url_template 和 params，返回一个新的 RequestParameter。
        原始 request_config 保持不变，可复用。

        params 示例：{"cat1": "tech", "cat2": "ai", "page": 1}
        """
        rc = self.template_request_config

        # TODO：下面可能缺错异常，但是估计没啥事
        # 路径参数填充
        filled_url = rc.url.format(**params)

        # query 参数：值可以是占位符字符串，也可以是普通值
        filled_params = {
            k: v.format(**params) if isinstance(v, str) else v  # 去掉多余的 str()
            for k, v in rc.params.items()
        }

        # bearer token 注入到 headers
        headers = dict(rc.headers)
        if rc.bearer_token:
            headers["Authorization"] = f"Bearer {rc.bearer_token}"

        return replace(         # 作用是浅拷贝一个 dataclass 实例，同时覆盖你指定的字段，其余字段原样保留。
            rc,
            url=filled_url,
            params=filled_params,
            headers=headers,
        )

    @abstractmethod
    def parse_response(self, response: "Response") -> ResponseParseResultEntity:
        """
        从响应中提取新闻链接
            各新闻源页面结构差异大，子类必须自行实现。
        """
        ...