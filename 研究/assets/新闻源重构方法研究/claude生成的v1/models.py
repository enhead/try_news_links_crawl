from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParseResult:
    """SourceConfig.parse_response 的返回值"""
    links: list[str]
    is_empty: bool


@dataclass
class CheckResult:
    """DbChecker.check_batch 的返回值"""
    existing: set[str]
    missing: list[str]
    exist_ratio: float


@dataclass
class NodeResult:
    """CrawlNode.execute 的返回值，叶子层的基础产出单元"""
    accumulated_params: dict[str, Any]   # 本次执行的完整坐标，用于断点恢复
    links_found: list[str]               # 本页解析出的全部链接
    links_new: list[str]                 # DB 中不存在的新链接
    is_empty: bool                       # 是否空页
    exist_ratio: float                   # 已存在比例，供 should_prune 使用


@dataclass
class LayerResult:
    """每层 execute 的返回值，向上冒泡汇总"""
    node_results: list[NodeResult] = field(default_factory=list)
    new_links: list[str] = field(default_factory=list)       # 汇总后去重的新链接
    total_requests: int = 0
    total_found: int = 0

    def merge(self, other: "LayerResult") -> None:
        """合并子层结果到当前层"""
        self.node_results.extend(other.node_results)
        self.new_links.extend(other.new_links)
        self.total_requests += other.total_requests
        self.total_found += other.total_found

    def dedup_links(self) -> None:
        seen = set()
        deduped = []
        for link in self.new_links:
            if link not in seen:
                seen.add(link)
                deduped.append(link)
        self.new_links = deduped


@dataclass
class CrawlResult:
    """SourceCrawler.crawl 的返回值"""
    source_id: str
    new_links: list[str]
    total_requests: int
    total_found: int
    last_checkpoint: dict[str, Any] | None = None  # 最后成功的坐标，用于断点恢复
