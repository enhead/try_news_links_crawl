"""节点角色值对象"""
from enum import Enum


class NodeRoleVO(str, Enum):
    """
    节点在结果树中的角色（与 Layer 类型无关）

    只有两种角色：
    - LEAF：实际执行 HTTP 请求的节点（发请求、解析、保存）
    - COMPOSITE：组织子节点的节点（无论是顺序、枚举、映射）
    """

    LEAF = "leaf"
    COMPOSITE = "composite"

    @property
    def is_leaf(self) -> bool:
        """是否是叶子节点"""
        return self == NodeRoleVO.LEAF

    @property
    def is_composite(self) -> bool:
        """是否是组合节点"""
        return self == NodeRoleVO.COMPOSITE
