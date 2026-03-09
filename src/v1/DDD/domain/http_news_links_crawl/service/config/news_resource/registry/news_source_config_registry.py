"""
新闻源配置注册表

提供装饰器注册机制，自动管理 resource_id 与配置类的映射关系。
"""

from typing import Dict, Type, List

from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import (
    AbstractNewsSourceConfig,
)


class NewsSourceConfigRegistry:
    """
    新闻源配置注册表

    使用装饰器模式注册新闻源配置类，支持根据 resource_id 查找对应的配置类。

    使用示例：
        @NewsSourceConfigRegistry.register("sg_straits_times")
        class StraitTimesConfig(AbstractNewsSourceConfig):
            ...

        # 获取配置类
        config_class = NewsSourceConfigRegistry.get_config_class("sg_straits_times")
    """

    _registry: Dict[str, Type[AbstractNewsSourceConfig]] = {}

    @classmethod
    def register(cls, resource_id: str):
        """
        装饰器：注册新闻源配置类

        Args:
            resource_id: 新闻源唯一标识，与数据库 news_source.resource_id 对应

        Returns:
            装饰器函数

        Raises:
            ValueError: 如果 resource_id 已被注册

        Example:
            @NewsSourceConfigRegistry.register("sg_straits_times")
            class StraitTimesConfig(AbstractNewsSourceConfig):
                ...
        """

        def decorator(config_class: Type[AbstractNewsSourceConfig]):
            if resource_id in cls._registry:
                raise ValueError(
                    f"配置类已注册: resource_id={resource_id}, "
                    f"已存在的类={cls._registry[resource_id].__name__}"
                )

            if not issubclass(config_class, AbstractNewsSourceConfig):
                raise TypeError(
                    f"配置类必须继承 AbstractNewsSourceConfig: {config_class.__name__}"
                )

            cls._registry[resource_id] = config_class
            return config_class

        return decorator

    @classmethod
    def get_config_class(cls, resource_id: str) -> Type[AbstractNewsSourceConfig]:
        """
        根据 resource_id 获取配置类

        Args:
            resource_id: 新闻源唯一标识

        Returns:
            配置类（未实例化）

        Raises:
            KeyError: 如果 resource_id 未注册
        """
        if resource_id not in cls._registry:
            raise KeyError(
                f"未找到配置类: resource_id={resource_id}. "
                f"已注册的 resource_id: {list(cls._registry.keys())}"
            )

        return cls._registry[resource_id]

    @classmethod
    def has_config(cls, resource_id: str) -> bool:
        """
        检查 resource_id 是否已注册

        Args:
            resource_id: 新闻源唯一标识

        Returns:
            是否已注册
        """
        return resource_id in cls._registry

    @classmethod
    def list_registered(cls) -> List[str]:
        """
        列出所有已注册的 resource_id
      Returns:
            已注册的 resource_id 列表
        """
        return list(cls._registry.keys())

    @classmethod
    def clear(cls):
        """
        清空注册表（主要用于测试）
        """
        cls._registry.clear()
