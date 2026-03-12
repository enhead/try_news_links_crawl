"""
依赖注入容器

职责：
- 注册所有依赖（配置、数据库、HTTP、Repository、Service）
- 管理依赖的生命周期（单例/工厂）
- 提供依赖获取接口

使用示例：
    # 创建容器
    container = AppContainer()

    # 获取应用服务
    app_service = container.news_crawl_application_service()

    # 加载新闻源配置（从 .env 读取）
    registered_ids = await app_service.load_all_source_configs()

    # 执行爬取
    result = await app_service.crawl_single_source("sg_straits_times")

    # 关闭资源
    await container.shutdown_resources()
"""

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from v1.DDD.app.src.main.config.app_config import AppConfig
from v1.DDD.domain.http_news_links_crawl.service.impl.news_crawl_application_service import NewsCrawlApplicationService
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.impl.news_link_crawl_service import NewsLinkCrawlService
from v1.DDD.infrastructure.http.httpx_adapter import HttpAdapter
from v1.DDD.infrastructure.persistent.repository.news_links_crawl_repository import (
    NewsLinksCrawlRepository,
)


class AppContainer(containers.DeclarativeContainer):
    """
    应用依赖容器

    职责：
    - 单例管理：配置、数据库引擎、HTTP 适配器
    - 工厂管理：Session、DAO、Repository、领域服务、应用服务

    依赖层次：
    配置（AppConfig）
      ├─ 数据库配置（DatabaseConfig）
      ├─ HTTP 配置（HttpConfig）
      └─ 新闻源配置（NewsSourceConfig）
          └─ 模块路径列表（从 .env 的 NEWS_SOURCE_MODULES 读取）

    基础设施层：
      ├─ 数据库引擎（单例）
      ├─ 数据库会话工厂（单例）
      └─ HTTP 适配器（单例）

    持久化层：
      ├─ DAO（工厂）
      └─ Repository（工厂）

    领域层：
      └─ 领域服务（工厂）

    应用层：
      └─ 应用服务（工厂）
    """

    # ========================================
    # 配置提供者（单例）
    # ========================================

    config = providers.Singleton(
        AppConfig.from_env,
        env_file=".env",
    )

    # ========================================
    # 基础设施层 - 单例（全局唯一）
    # ========================================

    # 数据库引擎（单例，复用连接池）
    db_engine = providers.Singleton(
        create_async_engine,
        url=config.provided.database.url,
        pool_size=config.provided.database.pool_size,
        pool_recycle=config.provided.database.pool_recycle,
        echo=config.provided.database.echo,
    )

    # 数据库会话工厂（单例）
    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # HTTP 适配器（单例，复用连接池）
    http_adapter = providers.Singleton(
        HttpAdapter,
        timeout=config.provided.http.timeout,
        connect_timeout=config.provided.http.connect_timeout,
        read_timeout=config.provided.http.read_timeout,
        write_timeout=config.provided.http.write_timeout,
        pool_timeout=config.provided.http.pool_timeout,
        max_connections=config.provided.http.max_connections,
        max_keepalive_connections=config.provided.http.max_keepalive_connections,
    )

    # ========================================
    # 持久化层 - 工厂（每次创建新实例）
    # ========================================

    # Repository 层（单例，无状态）
    news_crawl_repository = providers.Singleton(
        NewsLinksCrawlRepository,
        session_factory=db_session_factory,
    )

    # ========================================
    # 领域层 - 工厂
    # ========================================

    # 领域服务（工厂）
    news_link_crawl_service = providers.Factory(
        NewsLinkCrawlService,
    )

    # ========================================
    # 应用层 - 工厂
    # ========================================

    # 应用服务（工厂）
    news_crawl_application_service = providers.Factory(
        NewsCrawlApplicationService,
        repository=news_crawl_repository,
        http_adapter=http_adapter,
        crawl_service=news_link_crawl_service,
        news_source_config=config.provided.news_source,
    )

    # ========================================
    # 资源管理
    # ========================================
    # 注意：资源清理逻辑已移至 Application.shutdown() 方法
    # 因为 DeclarativeContainer 的自定义 async 方法可能无法正确执行
