from __future__ import annotations  # 这个似乎是有用的

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING


class AbstractLayer(ABC):
    """
    Layer 抽象基类。
    每个 Layer 持有下一层引用，自驱动遍历，自己决定是否短路。
    参数通过 accumulated_params 逐层积累向下传递，不跳层。
    """

    def __init__(self, key: str, next_layer: AbstractLayer | None = None):
        self.key = key                  # 当前层写入 accumulated_params 的 key
        self.next_layer = next_layer    # 下一层引用，叶子层为 None

    @abstractmethod
    def execute(
        self,
        accumulated_params: dict[str, Any],
        source_config: NewsSourceConfig,                # 传入新闻源的配置，layer和爬虫可能都需要
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
        checkpoint: dict[str, Any] | None = None,
    ) -> LayerResult:
        """
        主方法：获取当前层及以下所有新闻链接。
        负责遍历本层的值，调用 next_layer.execute()，汇总子结果。
        checkpoint 为上次中断时最后成功的 accumulated_params，用于断点恢复。
        """
        ...

    def _invoke_next(
        self,
        accumulated_params: dict[str, Any],
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
        checkpoint: dict[str, Any] | None,
    ) -> LayerResult:
        """调用下一层，或在叶子层直接执行 CrawlNode"""
        if self.next_layer is not None:
            return self.next_layer.execute(
                accumulated_params, source_config, http_adapter, db_checker, checkpoint
            )
        # 没有下一层时，当前层直接执行请求（理论上 SequentialLayer 才是叶子层）
        raise RuntimeError(f"{self.__class__.__name__} 没有 next_layer，无法执行请求")
