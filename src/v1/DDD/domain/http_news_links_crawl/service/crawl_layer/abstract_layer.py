"""
爬取层抽象基类。

定义 Layer 链中所有层的统一接口与通用行为：
  - execute()       主执行方法，子类必须实现
  - should_prune()  剪枝判断，默认不剪枝，SequentialLayer 等有状态的层按需覆写
  - next_layer      持有对下一层的引用，叶子层（SequentialLayer）此字段为 None

Layer 自驱动原则：
  每层负责遍历自己维度的值，对每个值追加到 factor.params 后，
  调用 next_layer.execute(new_factor) 向下递归；
  叶子层直接交给 CrawlNode 执行。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING



if TYPE_CHECKING:
    # 仅在类型检查阶段导入，避免循环依赖
    from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
    from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity


class AbstractCrawlLayer(ABC):
    """
    爬取层抽象基类。

    Attributes:
        key:        当前层负责的参数维度名，如 "cat1" / "page"
        next_layer: 下一层引用；叶子层（SequentialLayer）持有 CrawlNode 而非 Layer，此处为 None
    """

    def __init__(self, key: str, next_layer: AbstractCrawlLayer | None = None) -> None:
        """
        Args:
            key:        当前层的参数名
            next_layer: 链中的下一层；叶子层传 None
        """
        self.key = key
        self.next_layer = next_layer

    # ------------------------------------------------------------------ #
    #  核心接口                                                             #
    # ------------------------------------------------------------------ #

    @abstractmethod
    async def execute(self, factor: LayerFactorEntity) -> CrawlNodeResultEntity:
        """
        主执行方法：遍历本层所有值，递归驱动下层，汇总返回 LayerResult。

        实现约定：
          1. 遍历本层的值集合（固定列表 / 依赖映射 / 递增序列）
          2. 每个值调用 factor.with_param(self.key, value) 生成新 factor
          3. 将新 factor 传入 next_layer.execute() 或直接交给 CrawlNode
          4. 收集所有子结果，在适当时机调用 should_prune() 决定是否提前终止
          5. 汇总并返回 LayerResult

        Args:
            factor: 当前已积累的运行时参数，含基础设施上下文与上层传递的 params

        Returns:
            本层及以下所有节点的汇总结果
        """
        ...

    # ------------------------------------------------------------------ #
    #  剪枝钩子（默认不剪枝，子类按需覆写）                                   #
    # ------------------------------------------------------------------ #

    def should_prune(self, results_so_far: CrawlNodeResultEntity) -> bool:
        """
        根据已收集的子节点结果判断是否提前终止本层遍历。

        默认实现永远返回 False（不剪枝），适用于 EnumerableLayer / DependentLayer
        这类有限集合层，它们自然结束，无需剪枝。

        SequentialLayer 应覆写此方法，实现以下任意策略（可配置）：
          - 当前页为空页 → True
          - 当前页链接全部已存在于 DB → True
          - 已存在比例超过阈值 → True


        Returns:
            True 表示应立即停止遍历，False 表示继续
        """
        return False

    # ------------------------------------------------------------------ #
    #  链式构建辅助                                                          #
    # ------------------------------------------------------------------ #

    def set_next(self, layer: AbstractCrawlLayer) -> AbstractCrawlLayer:
        """
        设置下一层引用，支持链式调用。

        示例：
            enumerable.set_next(dependent).set_next(sequential)

        Args:
            layer: 下一层实例

        Returns:
            传入的 layer，便于继续链式调用
        """
        self.next_layer = layer
        return layer

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"key={self.key!r}, "
            f"next={self.next_layer.__class__.__name__ if self.next_layer else None}"
            f")"
        )


# TODO：先放这里，后面我会放在该放的地方，不着急，这里很多都是草稿，不是最终的
#
# @CrawlLayerFactory.register(LayerTypeConstants.ENUMERABLE)
# class EnumerableCrawlLayer(AbstractCrawlLayer):
#     """
#     枚举层：遍历固定值列表。
#     values: list[str]  e.g. ["tech", "finance"]
#     """
#
#     def __init__(self, key: str, values: list[str], next_layer: AbstractCrawlLayer | None = None):
#         super().__init__(key, next_layer)
#         self.values: list[str] = values
#
#     def execute(self, request: LayerFactorEntity) -> list[CrawlNodeResultEntity]:
#         results = []
#         for v in self.values:
#             results += self.next_layer.execute(request.with_param(self.key, v))
#         return results
#
#
#
# @CrawlLayerFactory.register(LayerTypeConstants.DEPENDENT)
# class DependentCrawlLayer(AbstractCrawlLayer):
#     """
#     依赖层：根据父层已积累的值，查 mapping 决定本层遍历哪些值。
#     values: {
#         "parent_key": "cat1",
#         "mapping": {"tech": ["ai", "mobile"], ...}
#     }
#     """
#
#     def __init__(self, key: str, values: dict, next_layer: AbstractCrawlLayer | None = None):
#         super().__init__(key, next_layer)
#         self.parent_key: str = values["parent_key"]
#         self.mapping: dict[str, list[str]] = values["mapping"]
#
#     def execute(self, request: LayerFactorEntity) -> list[CrawlNodeResultEntity]:
#         parent_val = request.params[self.parent_key]
#         results = []
#         for v in self.mapping.get(parent_val, []):
#             results += self.next_layer.execute(request.with_param(self.key, v))
#         return results
#
#
# @CrawlLayerFactory.register(LayerTypeConstants.SEQUENTIAL)
# class SequentialCrawlLayer(AbstractCrawlLayer):
#     """
#     顺序翻页层：从 start 开始步进，每页执行一个 CrawlNode，触发剪枝则停止。
#     叶子层，没有 next_layer。
#     values: {"start": 1, "step": 1}
#     """
#
#     def __init__(self, key: str, values: dict, next_layer: AbstractCrawlLayer | None = None):
#         super().__init__(key, next_layer=None)   # 强制叶子
#         self.start: int = values["start"]
#         self.step: int  = values["step"]
#
#     def execute(self, request: LayerFactorEntity) -> list[CrawlNodeResultEntity]:
#         results = []
#         page = self.start
#         while True:
#             result = CrawlNode(request.with_param(self.key, page)).execute()
#             results.append(result)
#             if self._should_prune(result):
#                 break
#             page += self.step
#         return results
#
#     def _should_prune(self, result: CrawlNodeResultEntity) -> bool:
#         return result.is_empty or result.exist_ratio >= 0.8