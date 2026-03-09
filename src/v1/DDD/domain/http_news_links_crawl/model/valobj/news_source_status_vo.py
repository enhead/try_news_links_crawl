from enum import Enum


class NewsSourceStatusVO(Enum):
    """新闻源状态值对象"""
    NORMAL = (0, "正常调度")
    DISABLED = (1, "手动停用")
    PARSE_ERROR = (2, "解析异常（连续失败后自动标记）")

    def __init__(self, code: int, desc: str):
        self.code = code
        self.desc = desc

    @classmethod
    def from_code(cls, code: int) -> "NewsSourceStatusVO":
        """从数据库整数值创建状态对象"""
        for status in cls:
            if status.code == code:
                return status
        raise ValueError(f"无效的状态码: {code}，有效值为 0/1/2")


