from __future__ import annotations  # 这个似乎是有用的

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import LayerNodeResultEntity
from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.factory.layer_factory import CrawlLayerFactory, LayerTypeConstants


class AbstractCrawlLayer(ABC):
    """
    Layer 抽象基类。
    每个 Layer 持有下一层引用，自驱动遍历，自己决定是否短路。
    参数通过 LayerRequest.params 逐层积累向下传递，不跳层。
    """

    def __init__(self, key: str, next_layer: AbstractCrawlLayer | None = None):
        self.key = key
        self.next_layer = next_layer

    @abstractmethod
    def execute(self, request: LayerFactorEntity) -> list[LayerNodeResultEntity]:
        """遍历本层的值，驱动下一层或叶子节点执行，汇总并返回结果"""
        ...



# TODO：先放这里，后面我会放在该放的地方，不着急，这里很多都是草稿，不是最终的

@CrawlLayerFactory.register(LayerTypeConstants.ENUMERABLE)
class EnumerableCrawlLayer(AbstractCrawlLayer):
    """
    枚举层：遍历固定值列表。
    values: list[str]  e.g. ["tech", "finance"]
    """

    def __init__(self, key: str, values: list[str], next_layer: AbstractCrawlLayer | None = None):
        super().__init__(key, next_layer)
        self.values: list[str] = values

    def execute(self, request: LayerFactorEntity) -> list[LayerNodeResultEntity]:
        results = []
        for v in self.values:
            results += self.next_layer.execute(request.with_param(self.key, v))
        return results



@CrawlLayerFactory.register(LayerTypeConstants.DEPENDENT)
class DependentCrawlLayer(AbstractCrawlLayer):
    """
    依赖层：根据父层已积累的值，查 mapping 决定本层遍历哪些值。
    values: {
        "parent_key": "cat1",
        "mapping": {"tech": ["ai", "mobile"], ...}
    }
    """

    def __init__(self, key: str, values: dict, next_layer: AbstractCrawlLayer | None = None):
        super().__init__(key, next_layer)
        self.parent_key: str = values["parent_key"]
        self.mapping: dict[str, list[str]] = values["mapping"]

    def execute(self, request: LayerFactorEntity) -> list[LayerNodeResultEntity]:
        parent_val = request.params[self.parent_key]
        results = []
        for v in self.mapping.get(parent_val, []):
            results += self.next_layer.execute(request.with_param(self.key, v))
        return results


@CrawlLayerFactory.register(LayerTypeConstants.SEQUENTIAL)
class SequentialCrawlLayer(AbstractCrawlLayer):
    """
    顺序翻页层：从 start 开始步进，每页执行一个 CrawlNode，触发剪枝则停止。
    叶子层，没有 next_layer。
    values: {"start": 1, "step": 1}
    """

    def __init__(self, key: str, values: dict, next_layer: AbstractCrawlLayer | None = None):
        super().__init__(key, next_layer=None)   # 强制叶子
        self.start: int = values["start"]
        self.step: int  = values["step"]

    def execute(self, request: LayerFactorEntity) -> list[LayerNodeResultEntity]:
        results = []
        page = self.start
        while True:
            result = CrawlNode(request.with_param(self.key, page)).execute()
            results.append(result)
            if self._should_prune(result):
                break
            page += self.step
        return results

    def _should_prune(self, result: LayerNodeResultEntity) -> bool:
        return result.is_empty or result.exist_ratio >= 0.8