from dataclasses import dataclass, field


@dataclass
class DiscoveredNewsLinkUrl:
    """
    一次请求中发现的单条新闻链接，对应 news_link 表一行的爬取产出部分。

    只描述"发现了什么"，不携带归属信息（source_id 由 SourceConfig 持有）。
    """

    url: str          # 新闻页面链接，最终写入 news_link.url
    crawl_params: dict  # 发现此 URL 时的完整参数快照，如 {"cat1":"tech","page":3}
                        # 写入 news_link.crawl_params，仅用于排障复现，不参与业务逻辑


@dataclass
class CrawlNodeResultEntity:
    """
    单次爬取节点的结果，同时也是所有 Layer 的统一返回对象。

    Layer 链执行完毕后，每层的结果通过 children 向上冒泡汇总，
    最顶层拿到的就是整棵树的完整产出。

    原始事实字段（urls_found / urls_new）直接存储，
    派生值（is_empty / exist_ratio）通过 @property 按需计算，不占存储。
    """

    # TODO：这里感觉还要加个状态位

    # 本页 HTTP 响应解析出的全部 URL，不论新旧，来自 parse_response()
    urls_found: list[DiscoveredNewsLinkUrl]

    # urls_found 中不在 DB 里的部分，来自 check_exists_batch()
    # 可直接作为 save_batch() 的入参，无需二次转换
    urls_new: list[DiscoveredNewsLinkUrl]

    # 子节点结果列表，由上层 Layer 在汇总时填入，叶子节点默认为空
    children: list["CrawlNodeResultEntity"] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """本页解析出的 URL 数为 0，SequentialLayer 据此判断分页自然结束。"""
        return len(self.urls_found) == 0

    @property
    def exist_ratio(self) -> float:
        """
        urls_found 中已存在于 DB 的比例，范围 [0.0, 1.0]。
        SequentialLayer 据此判断"重复率超过阈值 → 剪枝停止翻页"。
        urls_found 为空时返回 0.0，不触发剪枝。
        """
        total = len(self.urls_found)
        if total == 0:
            return 0.0
        return (total - len(self.urls_new)) / total

    def __add__(self, other: "CrawlNodeResultEntity") -> "CrawlNodeResultEntity":
        """支持加号运算符合并两个结果。"""
        return CrawlNodeResultEntity(
            urls_found=self.urls_found + other.urls_found,
            urls_new=self.urls_new + other.urls_new,
            children=self.children + other.children,
        )

    @classmethod
    def merge_all(cls, results: list["CrawlNodeResultEntity"]) -> "CrawlNodeResultEntity":
        """合并多个结果到单个对象，children 字段保存原始结果列表。"""
        all_urls_found: list[DiscoveredNewsLinkUrl] = []
        all_urls_new: list[DiscoveredNewsLinkUrl] = []

        for result in results:
            all_urls_found.extend(result.urls_found)
            all_urls_new.extend(result.urls_new)

        return cls(
            urls_found=all_urls_found,
            urls_new=all_urls_new,
            children=results,
        )

    @classmethod
    def empty(cls) -> "CrawlNodeResultEntity":
        """创建空结果对象。"""
        return cls(urls_found=[], urls_new=[], children=[])