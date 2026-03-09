"""
新闻源配置工厂类

支持从多种数据源加载新闻源元数据：
- 数据库（通过 INewsSourceRepository）
- JSON 配置文件
- 字典数据


TODO：
- 如果目前只有这个功能话有点鸡肋
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata

if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import INewsCrawlRepository


class NewsSourceConfigFactory:
    """
    新闻源配置工厂类。

    提供多种方式加载新闻源元数据：
    - load_metadata_from_repository(): 从数据库加载（通过 Repository 接口）
    - load_metadata_from_json(): 从 JSON 文件加载
    - load_metadata_from_dict(): 从字典构造

    注意：工厂只负责加载元数据（NewsSourceMetadata），
    具体的 layer_schema 和 template_request_config 仍需要在
    具体的新闻源配置子类中定义。
    """

    @staticmethod
    async def load_metadata_from_repository(
        resource_id: str,
        repository: "INewsCrawlRepository"
    ) -> NewsSourceMetadata:
        """
        从数据库加载新闻源元数据（通过 Repository 接口）。

        Args:
            resource_id: 新闻源唯一标识
            repository: 新闻爬虫仓储接口实现

        Returns:
            NewsSourceMetadata 对象

        Raises:
            ValueError: 如果数据库中不存在该新闻源
        """
        metadata = await repository.get_source_by_resource_id(resource_id)
        if metadata is None:
            raise ValueError(f"数据库中不存在 resource_id={resource_id} 的新闻源")
        return metadata

    @staticmethod
    def load_metadata_from_json(json_path: str | Path) -> NewsSourceMetadata:
        """
        从 JSON 文件加载新闻源元数据。

        JSON 文件格式示例：
        {
            "resource_id": "sg_straits_times",
            "name": "The Straits Times",
            "domain": "straitstimes.com",
            "url": "https://www.straitstimes.com",
            "country": "SG",
            "language": "en",
            "status": 0
        }

        Args:
            json_path: JSON 文件路径

        Returns:
            NewsSourceMetadata 对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: JSON 格式错误或缺少必需字段
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {json_path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return NewsSourceConfigFactory.load_metadata_from_dict(data)

    @staticmethod
    def load_metadata_from_dict(data: dict) -> NewsSourceMetadata:
        """
        从字典构造新闻源元数据。

        Args:
            data: 包含元数据字段的字典

        Returns:
            NewsSourceMetadata 对象

        Raises:
            ValueError: 缺少必需字段或字段值无效
        """
        required_fields = ["resource_id", "name", "domain", "url", "country", "language"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")

        return NewsSourceMetadata(
            resource_id=data["resource_id"],
            name=data["name"],
            domain=data["domain"],
            url=data["url"],
            country=data["country"],
            language=data["language"],
            status=data.get("status", 0),  # 默认为正常状态
        )
