"""节点停止原因值对象"""
from enum import Enum


class StopReasonVO(str, Enum):
    """
    节点停止执行的原因（通用设计，所有 Layer 都可以使用）

    当前实现：
    - SequentialLayer 会使用 NATURAL_END / PRUNED_BY_RATIO 等
    - EnumerableLayer 简单标记为 COMPLETED

    未来扩展：
    - MappingLayer 可能需要 CONDITION_NOT_MET（条件不满足）
    - ParallelLayer 可能需要 PARTIAL_FAILURE（部分失败）
    - 任何 Layer 都可以根据需要使用或扩展
    """

    # 正常结束
    COMPLETED = "completed"              # 全部执行完成
    NATURAL_END = "natural_end"          # 自然结束（如空结果）

    # 剪枝/优化停止
    PRUNED_BY_RATIO = "pruned_ratio"     # 重复率剪枝
    PRUNED_BY_DEPTH = "pruned_depth"     # 深度限制
    PRUNED_BY_COUNT = "pruned_count"     # 数量限制

    # 条件停止（未来可能用到）
    CONDITION_NOT_MET = "condition_not_met"  # 条件不满足

    # 错误中断
    HTTP_ERROR = "http_error"            # HTTP 错误
    PARSE_ERROR = "parse_error"          # 解析错误
    TIMEOUT = "timeout"                  # 超时

    # 外部控制（未来可能用到）
    USER_ABORT = "user_abort"            # 用户中止
    QUOTA_EXCEEDED = "quota_exceeded"    # 配额超限

    # 未停止
    NOT_STOPPED = "not_stopped"

    @property
    def is_natural_end(self) -> bool:
        """是否自然结束"""
        return self in (StopReasonVO.COMPLETED, StopReasonVO.NATURAL_END)

    @property
    def is_pruned(self) -> bool:
        """是否被剪枝"""
        return self in (
            StopReasonVO.PRUNED_BY_RATIO,
            StopReasonVO.PRUNED_BY_DEPTH,
            StopReasonVO.PRUNED_BY_COUNT,
        )

    @property
    def is_error(self) -> bool:
        """是否因错误停止"""
        return self in (
            StopReasonVO.HTTP_ERROR,
            StopReasonVO.PARSE_ERROR,
            StopReasonVO.TIMEOUT,
        )
