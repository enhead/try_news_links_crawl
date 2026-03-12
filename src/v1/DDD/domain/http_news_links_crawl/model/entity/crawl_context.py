"""
爬取上下文对象。

封装整条 Layer 链共享的基础设施引用，作为不可变容器在链中传递。
将基础设施集中在此，好处在于：
  - Layer 链签名稳定：扩展基础设施只改 CrawlContext，不影响 LayerFactorEntity
  - 依赖关系清晰：Layer 只感知 Factor，Factor 只感知 Context
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import INewsCrawlRepository
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import \
    AbstractNewsSourceConfig
from v1.DDD.infrastructure.http.httpx_adapter import HttpAdapter

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class CrawlContext:
    """
    Layer 链执行时的基础设施上下文（不可变值对象）。

    整条链共享同一个 CrawlContext 实例，不随层级深入而变化。

    Attributes:
        source_config:         新闻源配置，提供 build_request / parse_response 能力
        http_adapter:          HTTP 请求适配器，负责实际网络通信与重试
        news_crawl_repository: 新闻链接数据库操作接口，用于去重查询与剪枝判断
        session:               数据库会话，由 Application Service 创建并管理事务
    """

    source_config: AbstractNewsSourceConfig
    http_adapter: HttpAdapter
    news_crawl_repository: INewsCrawlRepository
    session: "AsyncSession"  # 🎯 改为 session，由外部管理

    def __repr__(self) -> str:
        # 只展示类型名，避免打印基础设施内部细节
        return (
            f"CrawlContext("
            f"source={self.source_config.__class__.__name__}, "
            f"adapter={self.http_adapter.__class__.__name__}, "
            f"repository={self.news_crawl_repository.__class__.__name__}"
            f")"
        )