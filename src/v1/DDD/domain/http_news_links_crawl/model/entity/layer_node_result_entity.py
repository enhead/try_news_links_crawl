"""爬取节点结果实体"""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import LayerType

from v1.DDD.domain.http_news_links_crawl.model.entity.execution_phase_entity import NewsExecutionPhaseEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj.node_role_vo import NodeRoleVO
from v1.DDD.domain.http_news_links_crawl.model.valobj.node_status_vo import NodeStatusVO
from v1.DDD.domain.http_news_links_crawl.model.valobj.stop_reason_vo import StopReasonVO


# TODO：还需要研究下：多次重复的情况，日志的输出感觉也一般

@dataclass
class DiscoveredNewsLinkUrl:
    """
    一次请求中发现的单条新闻链接，对应 news_link 表一行的爬取产出部分。

    只描述"发现了什么"，不携带归属信息（source_id 由 SourceConfig 持有）。
    """

    url: str          # 新闻页面链接，最终写入 news_link.url
    crawl_params: dict  # 发现此 URL 时的完整参数快照，如 {"cat1":"tech","page":3}
                        # 写入 news_link.crawl_params，仅用于排障复现，不参与业务逻辑
    category: str     # 栏目分类，如 "Politics", "Technology"
                      # 由 source_config.extract_category(crawl_params) 提取后填入


@dataclass
class CrawlNodeResultEntity:
    """
    爬取节点的执行结果

    设计原则：
    1. 节点角色（LEAF/COMPOSITE）决定结构
    2. Layer 类型（SEQUENTIAL/ENUMERABLE）仅用于标识
    3. 停止原因适用于所有节点类型
    4. 执行阶段（ExecutionPhase）仅叶子节点有值
    5. 聚合统计从子节点累加或自身计算
    """

    # ===== 节点身份 =====
    node_role: NodeRoleVO                      # 节点角色（LEAF / COMPOSITE）
    layer_type: "LayerType | None"           # Layer 类型（仅 COMPOSITE 有值，用于调试）

    # ===== 执行状态 =====
    status: NodeStatusVO                       # 执行状态（SUCCESS / HTTP_ERROR 等）
    stop_reason: StopReasonVO | None = None    # 停止原因（可选，主要用于 SequentialLayer）

    # ===== 执行详情（仅 LEAF 有值）=====
    execution: NewsExecutionPhaseEntity | None = None

    # ===== 子节点（仅 COMPOSITE 有值）=====
    children: list["CrawlNodeResultEntity"] = field(default_factory=list)

    # ===== 聚合统计（所有节点都有）=====
    total_requests: int = 0          # 总请求数
    success_requests: int = 0        # 成功请求数
    failed_requests: int = 0         # 失败请求数
    total_links_found: int = 0       # 总共发现的链接数
    total_links_new: int = 0         # 新增链接数

    # ===== 性能指标 =====
    duration_ms: int = 0             # 耗时（毫秒）

    # ===== 私有缓存字段（延迟计算 + 自动缓存）=====
    _urls_found_cache: list[DiscoveredNewsLinkUrl] | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _urls_new_cache: list[DiscoveredNewsLinkUrl] | None = field(
        default=None, init=False, repr=False, compare=False
    )

    # ===== 兼容属性（向后兼容）=====

    @property
    def urls_found(self) -> list[DiscoveredNewsLinkUrl]:
        """
        向后兼容：获取发现的所有链接（延迟计算 + 自动缓存）

        - 叶子节点：从 execution.urls_found 获取
        - 组合节点：从所有叶子子节点汇总
        - 性能优化：首次访问时计算并缓存，后续访问直接返回缓存
        """
        if self._urls_found_cache is None:
            if self.node_role == NodeRoleVO.LEAF and self.execution:
                self._urls_found_cache = self.execution.urls_found
            else:
                # 递归收集所有叶子节点的链接
                self._urls_found_cache = []
                for child in self.children:
                    self._urls_found_cache.extend(child.urls_found)
        return self._urls_found_cache

    @property
    def urls_new(self) -> list[DiscoveredNewsLinkUrl]:
        """
        向后兼容：获取新链接（延迟计算 + 自动缓存）

        - 叶子节点：从 execution.urls_new 获取
        - 组合节点：从所有叶子子节点汇总
        - 性能优化：首次访问时计算并缓存，后续访问直接返回缓存
        """
        if self._urls_new_cache is None:
            if self.node_role == NodeRoleVO.LEAF and self.execution:
                self._urls_new_cache = self.execution.urls_new
            else:
                # 递归收集所有叶子节点的新链接
                self._urls_new_cache = []
                for child in self.children:
                    self._urls_new_cache.extend(child.urls_new)
        return self._urls_new_cache

    @property
    def is_empty(self) -> bool:
        """
        向后兼容：是否空结果

        - 叶子节点：从 execution 判断
        - 组合节点：所有子节点都为空
        """
        if self.node_role == NodeRoleVO.LEAF and self.execution:
            return self.execution.is_empty_result
        else:
            return all(child.is_empty for child in self.children)

    @property
    def exist_ratio(self) -> float:
        """
        向后兼容：重复率

        - 叶子节点：从 execution.exist_ratio 获取
        - 组合节点：所有链接的平均重复率
        """
        if self.node_role == NodeRoleVO.LEAF and self.execution:
            return self.execution.exist_ratio
        else:
            if self.total_links_found == 0:
                return 0.0
            return (self.total_links_found - self.total_links_new) / self.total_links_found

    def compute_stats(self) -> None:
        """
        计算或聚合统计信息

        - 叶子节点：从 execution 计算
        - 组合节点：从 children 聚合
        """
        if self.node_role == NodeRoleVO.LEAF and self.execution:
            # 叶子节点：计算自身统计
            self.total_requests = 1
            self.success_requests = 1 if self.status.is_success else 0
            self.failed_requests = 0 if self.status.is_success else 1
            self.total_links_found = self.execution.links_found_count
            self.total_links_new = self.execution.links_new_count
        else:
            # 组合节点：从子节点聚合
            self.total_requests = sum(c.total_requests for c in self.children)
            self.success_requests = sum(c.success_requests for c in self.children)
            self.failed_requests = sum(c.failed_requests for c in self.children)
            self.total_links_found = sum(c.total_links_found for c in self.children)
            self.total_links_new = sum(c.total_links_new for c in self.children)
            self.duration_ms = sum(c.duration_ms for c in self.children)

    @classmethod
    def create_leaf(
        cls,
        status: NodeStatusVO,
        execution: NewsExecutionPhaseEntity,
        stop_reason: StopReasonVO | None = None,
        duration_ms: int = 0,
    ) -> "CrawlNodeResultEntity":
        """
        创建叶子节点结果

        Args:
            status: 执行状态
            execution: 执行阶段详情
            stop_reason: 停止原因（可选）
            duration_ms: 耗时（毫秒）

        Returns:
            叶子节点结果
        """
        result = cls(
            node_role=NodeRoleVO.LEAF,
            layer_type=None,
            status=status,
            stop_reason=stop_reason,
            execution=execution,
            duration_ms=duration_ms,
        )
        result.compute_stats()
        return result

    @classmethod
    def create_composite(
        cls,
        layer_type: "LayerType",
        children: list["CrawlNodeResultEntity"],
        stop_reason: StopReasonVO | None = None,
    ) -> "CrawlNodeResultEntity":
        """
        创建组合节点结果

        Args:
            layer_type: Layer 类型
            children: 子节点列表
            stop_reason: 停止原因（可选）

        Returns:
            组合节点结果
        """
        # 根据子节点判断状态
        if not children:
            status = NodeStatusVO.SUCCESS
        else:
            success_count = sum(1 for c in children if c.status.is_success)
            total_count = len(children)

            if success_count == total_count:
                status = NodeStatusVO.SUCCESS
            elif success_count == 0:
                # 所有子节点都失败，取第一个失败节点的状态
                status = next(c.status for c in children if not c.status.is_success)
            else:
                status = NodeStatusVO.PARTIAL_SUCCESS

        result = cls(
            node_role=NodeRoleVO.COMPOSITE,
            layer_type=layer_type,
            status=status,
            stop_reason=stop_reason,
            children=children,
        )
        result.compute_stats()
        return result

    @classmethod
    def empty(cls) -> "CrawlNodeResultEntity":
        """
        创建空结果对象（向后兼容）

        Returns:
            空的叶子节点结果
        """
        return cls.create_leaf(
            status=NodeStatusVO.EMPTY_RESULT,
            execution=NewsExecutionPhaseEntity(),
            stop_reason=StopReasonVO.NATURAL_END,
        )

    def collect_leaf_nodes(self) -> list["CrawlNodeResultEntity"]:
        """
        递归收集所有叶子节点

        Returns:
            叶子节点列表
        """
        if self.node_role == NodeRoleVO.LEAF:
            return [self]
        else:
            leaves = []
            for child in self.children:
                leaves.extend(child.collect_leaf_nodes())
            return leaves

    @classmethod
    def merge_all(cls, results: list["CrawlNodeResultEntity"]) -> "CrawlNodeResultEntity":
        """
        向后兼容：合并多个结果节点为一个组合节点

        注意：此方法已被 create_composite() 取代，仅为向后兼容保留。
        推荐使用 create_composite() 以获得更好的类型标识和停止原因追踪。

        Args:
            results: 待合并的结果节点列表

        Returns:
            合并后的组合节点（使用 ENUMERABLE 作为默认 layer_type）
        """
        if not results:
            return cls.empty()

        # 使用 create_composite 实现，默认使用 ENUMERABLE 类型
        from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import LayerType

        return cls.create_composite(
            layer_type=LayerType.ENUMERABLE,
            children=results,
            stop_reason=None,
        )
