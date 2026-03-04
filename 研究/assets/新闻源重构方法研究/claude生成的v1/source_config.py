from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from news_crawler.http_adapter import Response
from news_crawler.models import ParseResult

if TYPE_CHECKING:
    from news_crawler.layer import Layer


@dataclass
class RequestConfig:
    url_template: str                            # 如 "https://example.com/{cat1}/{cat2}?page={page}"
    method: str = "GET"
    headers: dict[str, str] | None = None
    timeout: int = 10


@dataclass
class ParseConfig:
    type: str                                    # "css" | "jsonpath" | "regex"
    rule: str                                    # 具体规则，如 CSS 选择器
    attr: str = "href"                           # 取元素的哪个属性


class SourceConfig:
    def __init__(
        self,
        source_id: str,
        root_layer: "Layer",
        request_config: RequestConfig,
        parse_config: ParseConfig,
    ):
        self.source_id = source_id
        self.root_layer = root_layer
        self.request_config = request_config
        self.parse_config = parse_config

    def build_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        将积累的遍历参数填入 URL 模板，生成完整请求参数。
        params 如 {cat1: "tech", cat2: "ai", page: 1}
        """
        url = self.request_config.url_template.format(**params)
        return {
            "url": url,
            "method": self.request_config.method,
            "headers": self.request_config.headers or {},
            "timeout": self.request_config.timeout,
        }

    def parse_response(self, response: Response) -> ParseResult:
        """
        从 HTTP 响应中提取新闻链接列表。
        根据 parse_config 的类型分派到具体解析逻辑。
        """
        if self.parse_config.type == "css":
            return self._parse_css(response)
        elif self.parse_config.type == "jsonpath":
            return self._parse_jsonpath(response)
        elif self.parse_config.type == "regex":
            return self._parse_regex(response)
        else:
            raise ValueError(f"不支持的解析类型: {self.parse_config.type}")

    def _parse_css(self, response: Response) -> ParseResult:
        # TODO: 使用 BeautifulSoup 按 CSS 选择器提取链接
        raise NotImplementedError

    def _parse_jsonpath(self, response: Response) -> ParseResult:
        # TODO: 使用 jsonpath 表达式提取链接
        raise NotImplementedError

    def _parse_regex(self, response: Response) -> ParseResult:
        # TODO: 使用正则表达式提取链接
        raise NotImplementedError
