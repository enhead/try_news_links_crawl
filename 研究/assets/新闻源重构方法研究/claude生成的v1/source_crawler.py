from typing import Any

from news_crawler.db_checker import DbChecker
from news_crawler.http_adapter import HttpAdapter
from news_crawler.models import CrawlResult
from news_crawler.source_config import SourceConfig


class SourceCrawler:
    """
    单源爬虫入口，非常薄。
    职责：调用 root_layer.execute()，拿到顶层 LayerResult，封装成 CrawlResult。
    遍历、短路、结果收集全部由 Layer 链内部自驱动完成。
    """

    def __init__(
        self,
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
    ):
        self.source_config = source_config
        self.http_adapter = http_adapter
        self.db_checker = db_checker

    def crawl(self, checkpoint: dict[str, Any] | None = None) -> CrawlResult:
        """
        增量爬取入口。
        checkpoint: 上次中断时最后成功的 accumulated_params，不传则从头开始。
        """
        layer_result = self.source_config.root_layer.execute(
            accumulated_params={},
            source_config=self.source_config,
            http_adapter=self.http_adapter,
            db_checker=self.db_checker,
            checkpoint=checkpoint,
        )

        # 最后一个成功的 NodeResult 的 params 即为新断点
        last_checkpoint = None
        if layer_result.node_results:
            last_checkpoint = layer_result.node_results[-1].accumulated_params

        return CrawlResult(
            source_id=self.source_config.source_id,
            new_links=layer_result.new_links,
            total_requests=layer_result.total_requests,
            total_found=layer_result.total_found,
            last_checkpoint=last_checkpoint,
        )
