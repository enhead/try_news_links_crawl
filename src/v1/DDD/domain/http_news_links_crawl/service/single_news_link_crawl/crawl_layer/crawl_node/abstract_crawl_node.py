

"""
爬取节点抽象基类。

定义单次 HTTP 请求的执行接口，具体实现由子类完成。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity


class AbstractCrawlNode(ABC):
    """
    爬取节点抽象基类。

    职责：
      - 定义单次爬取的执行接口
      - 持有运行时参数和基础设施上下文

    设计约束：
      - 不感知 Layer 链，不持有 next_layer
      - 只负责"一次请求"的完整流程
    """

    def __init__(self, factor: LayerFactorEntity) -> None:
        """
        Args:
            factor: 携带完整参数和基础设施上下文的运行时对象
        """
        self._factor = factor

    @abstractmethod
    async def fetch(self) -> CrawlNodeResultEntity:
        """
        仅请求和解析，不做数据库去重。

        流程：
          1. 构建请求参数
          2. 发送 HTTP 请求
          3. 解析响应

        适用场景：Layer 层需要批量去重时使用，提高数据库查询效率。

        Returns:
            urls_found: 解析出的所有 URL
            urls_new: 空列表（待 Layer 层批量去重）

        Raises:
            HttpRequestError: 网络层错误
            HttpStatusError: HTTP 4xx/5xx 错误
        """
        pass

    @abstractmethod
    async def execute(self) -> CrawlNodeResultEntity:
        """
        完整流程：请求 → 解析 → 去重。

        流程：
          1. 构建请求参数
          2. 发送 HTTP 请求
          3. 解析响应
          4. 批量去重
          5. 组装结果

        适用场景：单节点独立执行，需要立即知道新增 URL。

        Returns:
            urls_found: 解析出的所有 URL
            urls_new: 去重后的新增 URL

        Raises:
            HttpRequestError: 网络层错误
            HttpStatusError: HTTP 4xx/5xx 错误
        """
        pass