"""执行阶段详情实体"""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import DiscoveredNewsLinkUrl


@dataclass
class NewsExecutionPhaseEntity:
    """
    单次请求的执行阶段详细记录

    设计说明：
    - 仅用于叶子节点（实际执行 HTTP 请求的节点）
    - 记录完整的执行流程：请求 → 响应 → 解析 → 去重 → 保存
    - 所有字段都有默认值，根据执行阶段逐步填充
    """

    # ===== 请求阶段 =====
    request_params: dict = field(default_factory=dict)  # 请求参数，如 {"category": "politics", "page": 1}
    request_url: str = ""                               # 实际请求的 URL

    # ===== 响应阶段 =====
    response_status_code: int | None = None             # HTTP 状态码
    response_duration_ms: int = 0                       # 响应耗时（毫秒）

    # ===== 解析阶段 =====
    parse_status: str = ""                              # 解析状态："success" / "error"
    parse_error: str | None = None                      # 解析错误信息
    urls_found: list["DiscoveredNewsLinkUrl"] = field(default_factory=list)  # 解析出的链接

    # ===== 去重阶段 =====
    urls_new: list["DiscoveredNewsLinkUrl"] = field(default_factory=list)    # 新链接（不在数据库）
    exist_ratio: float = 0.0                            # 重复率 [0.0, 1.0]

    # ===== 保存阶段 =====
    saved_count: int = 0                                # 实际保存数量

    @property
    def links_found_count(self) -> int:
        """解析出的链接数量"""
        return len(self.urls_found)

    @property
    def links_new_count(self) -> int:
        """新链接数量"""
        return len(self.urls_new)

    @property
    def is_empty_result(self) -> bool:
        """是否空结果（解析成功但0条链接）"""
        return self.parse_status == "success" and self.links_found_count == 0
