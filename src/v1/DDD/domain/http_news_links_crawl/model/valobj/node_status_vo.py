"""节点执行状态值对象"""
from enum import Enum


class NodeStatusVO(str, Enum):
    """
    节点执行状态

    状态分类：
    - 成功状态：SUCCESS（有链接）、EMPTY_RESULT（无链接）
    - 部分成功：PARTIAL_SUCCESS（有子节点失败）
    - 错误状态：HTTP_ERROR、PARSE_ERROR
    """

    SUCCESS = "success"              # 成功（发现了链接）
    PARTIAL_SUCCESS = "partial"      # 部分成功（有子节点失败）
    HTTP_ERROR = "http_error"        # HTTP 请求失败
    PARSE_ERROR = "parse_error"      # 解析失败
    EMPTY_RESULT = "empty_result"    # 成功但0条链接

    @property
    def is_success(self) -> bool:
        """是否成功（包括成功但0条链接）"""
        return self in (NodeStatusVO.SUCCESS, NodeStatusVO.EMPTY_RESULT)

    @property
    def is_error(self) -> bool:
        """是否错误"""
        return self in (NodeStatusVO.HTTP_ERROR, NodeStatusVO.PARSE_ERROR)

    @property
    def is_partial_success(self) -> bool:
        """是否部分成功"""
        return self == NodeStatusVO.PARTIAL_SUCCESS
