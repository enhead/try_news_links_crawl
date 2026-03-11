"""
新闻源配置注册表

提供装饰器注册机制，管理 resource_id 与配置类的映射关系，
并支持单例模式的配置对象创建（需配合仓储接口完成 metadata 查询）。



TODO：待探究：
    - 此处应该是需要导入才会自动注册，没时间了，没法细看，后面需要想想


创建配置类 + @register 装饰
    ↓
在 __init__.py 中导入（触发注册）：只有导入这个具体实现的配置类文件的时候，才会触发注册
    ↓
调用 create_config() 获取单例实例
"""

from typing import Dict, List, Optional, Type

from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import (
    INewsCrawlRepository,
)
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import (
    AbstractNewsSourceConfig,
)


class NewsSourceConfigRegistry:
    """
    新闻源配置注册表

    两层能力：
    1. 纯注册表：装饰器注册 + 类查找（无副作用）
    2. 单例工厂：create_config 负责查 DB、实例化、缓存

    使用示例：
        @NewsSourceConfigRegistry.register("sg_straits_times")
        class StraitTimesConfig(AbstractNewsSourceConfig):
            ...

        # 仅获取类（不实例化）
        cls = NewsSourceConfigRegistry.get_config_class("sg_straits_times")

        # 获取单例实例（首次查 DB，后续走缓存）
        config = await NewsSourceConfigRegistry.create_config("sg_straits_times", repo)
    """

    _registry: Dict[str, Type[AbstractNewsSourceConfig]] = {}
    _instances: Dict[str, AbstractNewsSourceConfig] = {}

    @classmethod
    def register(cls, resource_id: str):
        """
        装饰器：注册新闻源配置类。

        Args:
            resource_id: 新闻源唯一标识，与数据库 news_source.resource_id 对应

        Raises:
            ValueError: resource_id 已被注册
            TypeError: 配置类未继承 AbstractNewsSourceConfig
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
        获取已注册的配置类（不实例化）。

        Args:
            resource_id: 新闻源唯一标识

        Raises:
            KeyError: resource_id 未注册
        """
        if resource_id not in cls._registry:
            raise KeyError(
                f"未找到配置类: resource_id={resource_id}，"
                f"已注册: {list(cls._registry.keys())}"
            )
        return cls._registry[resource_id]

    @classmethod
    async def create_config(
        cls, resource_id: str, repository: INewsCrawlRepository
    ) -> AbstractNewsSourceConfig:
        """
        获取配置对象（单例）。首次调用查询 DB 并实例化，后续返回缓存。

        Args:
            resource_id: 新闻源唯一标识
            repository: 数据仓储接口，用于查询 metadata

        Raises:
            KeyError: resource_id 未注册
            ValueError: 数据库中未找到对应新闻源
        """
        if resource_id in cls._instances:
            return cls._instances[resource_id]

        config_class = cls.get_config_class(resource_id)  # 未注册时抛 KeyError

        metadata = await repository.get_source_by_resource_id(resource_id)
        if metadata is None:
            raise ValueError(f"数据库中未找到新闻源: {resource_id}")

        instance = config_class(metadata=metadata)
        cls._instances[resource_id] = instance
        return instance

    @classmethod
    def has_config(cls, resource_id: str) -> bool:
        """检查 resource_id 是否已注册。"""
        return resource_id in cls._registry

    @classmethod
    def list_registered(cls) -> List[str]:
        """返回所有已注册的 resource_id（用于调试/监控）。"""
        return list(cls._registry.keys())

    @classmethod
    def clear_cache(cls, resource_id: Optional[str] = None) -> None:
        """
        清除实例缓存（不影响注册表）。主要用于测试或强制重载配置。

        Args:
            resource_id: 指定清除某个实例；None 则清除全部
        """
        if resource_id is None:
            cls._instances.clear()
        else:
            cls._instances.pop(resource_id, None)

    @classmethod
    def auto_register_from_module(
        cls,
        module_paths: str | list[str] | None = None
    ) -> list[str]:
        """
        自动扫描并注册所有新闻源配置类

        通过导入指定模块，触发所有装饰器（@NewsSourceConfigRegistry.register()）的执行

        注意：
        - 配置类必须在模块的 __init__.py 中导入
        - 配置类必须使用 @NewsSourceConfigRegistry.register() 装饰器

        Args:
            module_paths: 要导入的模块路径，支持：
                - None: 使用默认路径 ["v1.DDD.app.src.resource.news_source"]
                - str: 单个模块路径（如 "v1.DDD.app.src.resource.news_source"）
                - list[str]: 多个模块路径数组

        Returns:
            list[str]: 成功注册的 resource_id 列表

        Raises:
            ImportError: 模块导入失败
        """
        import importlib

        # 默认模块路径
        default_paths = ["v1.DDD.app.src.resource.news_source"]

        # 标准化为列表
        if module_paths is None:
            paths = default_paths
        elif isinstance(module_paths, str):
            paths = [module_paths]
        else:
            paths = module_paths

        # 记录导入前的注册数量
        before_count = len(cls._registry)
        failed_imports = []

        # 逐个导入模块
        for module_path in paths:
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                failed_imports.append((module_path, str(e)))

        # 如果有失败的导入，抛出异常
        if failed_imports:
            error_details = "\n".join(
                f"  - {path}: {error}"
                for path, error in failed_imports
            )
            raise ImportError(
                f"部分模块导入失败:\n{error_details}\n"
                f"请确保这些模块存在且路径正确"
            )

        # 计算新注册的数量
        new_count = len(cls._registry) - before_count

        # 返回所有已注册的 resource_id
        return cls.list_registered()

    @classmethod
    def clear_registry(cls) -> None:
        """清空注册表和实例缓存（仅用于测试）。"""
        cls._registry.clear()
        cls._instances.clear()