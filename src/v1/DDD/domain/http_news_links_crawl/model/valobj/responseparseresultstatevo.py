from enum import Enum

class ResponseParseResultStateVO(Enum):
    SUCCESS           = ("success",           "正常解析到链接")
    EMPTY_PAGE        = ("empty_page",        "空页（分页自然结束）")
    STRUCTURE_CHANGED = ("structure_changed", "站点结构变化（选择器失效）")
    PARTIAL_FAILURE   = ("partial_failure",   "部分条目解析失败")

    def __init__(self, code: str, desc: str):
        self.code = code
        self.desc = desc