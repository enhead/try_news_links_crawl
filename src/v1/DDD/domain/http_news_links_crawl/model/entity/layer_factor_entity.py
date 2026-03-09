"""
Layer 链运行时参数承载对象。

负责在整条 Layer 链的执行过程中向下传递两类数据：
  1. CrawlContext —— 基础设施引用，整条链共享，始终不变
  2. params       —— 累积遍历参数，每经过一层追加一个维度，逐层深化

典型调用链示意：
  factor                                     # params = {}
  → factor.with_param("cat1", "tech")        # params = {cat1: tech}
  → factor.with_param("cat2", "ai")          # params = {cat1: tech, cat2: ai}
  → factor.with_param("page", 1)             # params = {cat1: tech, cat2: ai, page: 1}
  → CrawlNode(factor).execute()

设计约束：
  - frozen=True 保证不可变，所有"修改"均返回新实例，天然线程安全
  - 无 id，无持久化语义，纯内存运行时对象（Value Object 语义）
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_context import CrawlContext


@dataclass(frozen=True)
class LayerFactorEntity:
    """
    Layer 链执行时的参数承载对象（运行时值对象，无持久化 id）。

    Attributes:
        context: 基础设施上下文，持有 source_config / http_adapter / repository
        params:  当前层路径上积累的遍历参数，key 为层的 key，value 为该层当前迭代值
    """

    context: CrawlContext
    params: dict[str, Any]

    # ------------------------------------------------------------------ #
    #  工厂方法                                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def create(cls, context: CrawlContext) -> LayerFactorEntity:
        """
        创建一个携带空参数的初始 Factor，用于 Layer 链的入口（SourceCrawler 调用）。

        Args:
            context: 爬取上下文，包含本次爬取所需的全部基础设施

        Returns:
            params 为空的初始 LayerFactorEntity
        """
        return cls(context=context, params={})

    # ------------------------------------------------------------------ #
    #  参数累积（不可变演进）                                                #
    # ------------------------------------------------------------------ #

    def with_param(self, key: str, value: Any) -> LayerFactorEntity:
        """
        追加单个遍历参数，返回新实例，原实例保持不变。

        每个 Layer 在将控制权交给 next_layer 前，先调用此方法把自己负责的
        维度写入 params，生成新的 Factor 向下传递。

        Args:
            key:   层的参数名，如 "cat1" / "page"
            value: 该层当前迭代的具体值

        Returns:
            包含新参数的 LayerFactorEntity 新实例
        """
        return replace(self, params={**self.params, key: value})

    def with_params(self, extra: dict[str, Any]) -> LayerFactorEntity:
        """
        批量追加遍历参数，返回新实例。

        适用于测试构造或需要一次性注入多个参数的场景。

        Args:
            extra: 要追加的参数字典，与现有 params 合并，同 key 时 extra 覆盖

        Returns:
            合并后的 LayerFactorEntity 新实例
        """
        return replace(self, params={**self.params, **extra})

    # ------------------------------------------------------------------ #
    #  便捷访问（透传 context 字段，减少链式调用）                            #
    # ------------------------------------------------------------------ #

    @property
    def source_config(self):
        """透传 context.source_config，减少 Layer 内部的 factor.context.xxx 链式访问。"""
        return self.context.source_config

    @property
    def http_adapter(self):
        """透传 context.http_adapter。"""
        return self.context.http_adapter

    @property
    def news_links_crawl_repository(self):
        """透传 context.news_links_crawl_repository。"""
        return self.context.news_crawl_repository

    # ------------------------------------------------------------------ #
    #  调试辅助                                                             #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        # 只展示参数路径与 context 摘要，基础设施内部细节不打印
        return (
            f"LayerFactorEntity("
            f"params={self.params}, "
            f"context={self.context!r}"
            f")"
        )