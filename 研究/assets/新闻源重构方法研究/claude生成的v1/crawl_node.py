from typing import Any

from news_crawler.db_checker import DbChecker
from news_crawler.http_adapter import HttpAdapter
from news_crawler.models import NodeResult
from news_crawler.source_config import SourceConfig


class CrawlNode:
    """
    单次请求执行单元。
    拿着当前积累的完整参数，执行请求 → 解析 → DB 检查，返回 NodeResult。
    """

    def __init__(
        self,
        params: dict[str, Any],
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
    ):
        self.params = params
        self.source_config = source_config
        self.http_adapter = http_adapter
        self.db_checker = db_checker

    def execute(self) -> NodeResult:
        # 1. 构造请求参数
        request_params = self.source_config.build_request(self.params)

        # 2. 发送请求
        response = self.http_adapter.send(request_params)

        # 3. 解析响应，提取链接
        parse_result = self.source_config.parse_response(response)

        # 4. 空页短路，不必再查 DB
        if parse_result.is_empty or not parse_result.links:
            return NodeResult(
                accumulated_params=self.params.copy(),
                links_found=[],
                links_new=[],
                is_empty=True,
                exist_ratio=0.0,
            )

        # 5. 批量查询 DB 存在性
        check_result = self.db_checker.check_batch(parse_result.links)

        return NodeResult(
            accumulated_params=self.params.copy(),
            links_found=parse_result.links,
            links_new=check_result.missing,
            is_empty=False,
            exist_ratio=check_result.exist_ratio,
        )
