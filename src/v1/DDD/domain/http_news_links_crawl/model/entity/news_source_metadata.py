"""
新闻源元数据实体。

封装新闻源的静态元数据信息，与 news_source 表结构对应。
可从数据库或配置文件加载，作为不可变值对象在系统中传递。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..valobj.news_source_status_vo import NewsSourceStatusVO



@dataclass(frozen=True)
class NewsSourceMetadata:
    """
    新闻源元数据（不可变值对象）。

    与数据库 news_source 表结构严格对应，支持从多种数据源加载：
    - 数据库（news_source 表）
    - JSON 配置文件
    - 代码硬编码

    Attributes:
        resource_id: 新闻源唯一标识，格式：{country}_{media_name}，如 "sg_straits_times"
        name: 媒体机构名称，如 "Vietnam News"
        domain: 域名，如 "vietnamnews.vn"
        url: 新闻页面 URL（备用）
        country: 国家代码（ISO 3166-1 alpha-2，如 "SG", "MY", "TH"）
        language: 语言代码（BCP 47，如 "en", "zh", "id", "th"）
        status: 新闻源状态（0-正常 1-停用 2-解析异常）
    """

    resource_id: str
    name: str
    domain: str
    url: str
    country: str
    language: str
    status: NewsSourceStatusVO = NewsSourceStatusVO.NORMAL

    def __post_init__(self) -> None:
        """验证字段有效性"""
        if not self.resource_id:
            raise ValueError("resource_id 不能为空")
        if not self.country or len(self.country) != 2:
            raise ValueError(f"country 必须是2位国家代码（ISO 3166-1 alpha-2），当前值: {self.country}")
        if not self.domain:
            raise ValueError("domain 不能为空")
        if not isinstance(self.status, NewsSourceStatusVO):
            raise ValueError(f"status 必须是 NewsSourceStatusVO 枚举类型，当前值: {self.status}")

    def is_active(self) -> bool:
        """判断新闻源是否可调度"""
        return self.status == NewsSourceStatusVO.NORMAL

    def __repr__(self) -> str:
        return (
            f"NewsSourceMetadata("
            f"resource_id={self.resource_id!r}, "
            f"country={self.country!r}, "
            f"name={self.name!r}, "
            f"status={self.status}"
            f")"
        )
