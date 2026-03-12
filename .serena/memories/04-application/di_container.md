# DI容器（依赖注入容器）

**最后更新**: 2026-03-11

## 概述

DI容器是应用层的核心基础设施，负责管理所有依赖的创建、配置和生命周期。

**使用的库**: `dependency-injector`

**核心优势**：
- ✅ **解耦**：各层独立，易于测试和替换
- ✅ **单例管理**：连接池复用，节省资源
- ✅ **工厂模式**：按需创建，避免浪费
- ✅ **生命周期管理**：统一关闭资源
- ✅ **配置驱动**：通过 `.env` 文件配置

## 容器结构

**文件**: `src/v1/DDD/app/src/main/DI/container.py`

### 依赖树

```
AppConfig (单例)
  ├─ DatabaseConfig
  │    ├─ host, port, user, password, database
  │    ├─ pool_size, pool_recycle, echo
  │    └─ url (动态生成: mysql+asyncmy://...)
  ├─ HttpConfig
  │    ├─ timeout, connect_timeout, read_timeout
  │    ├─ write_timeout, pool_timeout
  │    └─ max_connections, max_keepalive_connections
  └─ NewsSourceConfig
       └─ module_paths: list[str]

基础设施层（单例）：
  ├─ DbEngine (AsyncEngine)
  │    └─ 连接池（pool_size=10）
  ├─ DbSessionFactory (async_sessionmaker)
  │    └─ 创建 AsyncSession
  └─ HttpAdapter (httpx客户端)
       └─ 连接池（max_connections=100）

持久化层（单例）：
  └─ NewsLinksCrawlRepository
       └─ 使用 DbSessionFactory

领域层（工厂）：
  └─ NewsLinkCrawlService

应用层（工厂）：
  └─ NewsCrawlApplicationService
       ├─ repository
       ├─ http_adapter
       ├─ crawl_service
       └─ news_source_config
```

## 核心代码

```python
from dependency_injector import containers, providers

class AppContainer(containers.DeclarativeContainer):
    """应用依赖容器"""
    
    # ========== 配置（单例）==========
    config = providers.Singleton(
        AppConfig.from_env,
        env_file=".env",
    )
    
    # ========== 基础设施（单例）==========
    
    # 数据库引擎（全局唯一，复用连接池）
    db_engine = providers.Singleton(
        create_async_engine,
        url=config.provided.database.url,
        pool_size=config.provided.database.pool_size,
        pool_recycle=config.provided.database.pool_recycle,
        echo=config.provided.database.echo,
    )
    
    # 数据库会话工厂（全局唯一）
    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # HTTP 适配器（全局唯一，复用连接池）
    http_adapter = providers.Singleton(
        HttpAdapter,
        timeout=config.provided.http.timeout,
        connect_timeout=config.provided.http.connect_timeout,
        # ... 其他配置
    )
    
    # ========== 持久化层（单例）==========
    
    # Repository（单例，无状态）
    news_crawl_repository = providers.Singleton(
        NewsLinksCrawlRepository,
        session_factory=db_session_factory,
    )
    
    # ========== 领域层（工厂）==========
    
    # 领域服务（每次创建新实例）
    news_link_crawl_service = providers.Factory(
        NewsLinkCrawlService,
    )
    
    # ========== 应用层（工厂）==========
    
    # 应用服务（每次创建新实例）
    news_crawl_application_service = providers.Factory(
        NewsCrawlApplicationService,
        repository=news_crawl_repository,
        http_adapter=http_adapter,
        crawl_service=news_link_crawl_service,
        news_source_config=config.provided.news_source,
    )
    
    # ========== 资源管理 ==========
    
    async def shutdown_resources(self):
        """优雅关闭所有资源"""
        # 1. 关闭 HTTP 连接池
        http = self.http_adapter()
        if http and hasattr(http, 'close'):
            await http.close()
        
        # 2. 关闭数据库引擎（最重要）
        engine = self.db_engine()
        if engine:
            await engine.dispose()
```

## 单例 vs 工厂

### 单例（Singleton）

**何时使用**：
- 全局唯一的资源（数据库引擎、HTTP客户端）
- 需要复用连接池的组件
- 无状态的服务（Repository）
- 配置对象

**特点**：
- ✅ 只创建一次，全局复用
- ✅ 节省资源（连接池、内存）
- ✅ 线程安全
- ⚠️ 需要确保无状态或线程安全

**示例**：
```python
# 定义
db_engine = providers.Singleton(create_async_engine, ...)
http_adapter = providers.Singleton(HttpAdapter, ...)

# 使用（每次调用返回同一个实例）
engine1 = container.db_engine()
engine2 = container.db_engine()
assert engine1 is engine2  # True
```

### 工厂（Factory）

**何时使用**：
- 有状态的服务
- 需要隔离的组件
- 短生命周期的对象

**特点**：
- ✅ 每次创建新实例
- ✅ 状态隔离
- ⚠️ 可能消耗更多资源

**示例**：
```python
# 定义
news_crawl_application_service = providers.Factory(
    NewsCrawlApplicationService,
    ...
)

# 使用（每次调用返回新实例）
service1 = container.news_crawl_application_service()
service2 = container.news_crawl_application_service()
assert service1 is not service2  # True
```

## 依赖注入模式

### 构造器注入（推荐）

```python
class NewsCrawlApplicationService:
    def __init__(
        self,
        repository: BaseNewsLinksCrawlRepository,
        http_adapter: HttpAdapter,
        crawl_service: NewsLinkCrawlService,
        news_source_config: NewsSourceConfig,
    ):
        self.repository = repository
        self.http_adapter = http_adapter
        self.crawl_service = crawl_service
        self.news_source_config = news_source_config
```

**优势**：
- ✅ 依赖显式声明
- ✅ 易于测试（Mock依赖）
- ✅ 类型安全

### 容器注入（不推荐）

```python
# ❌ 不推荐：直接传入容器
class Service:
    def __init__(self, container: AppContainer):
        self.container = container
        self.repo = container.repository()  # 隐式依赖
```

**问题**：
- ❌ 依赖不明确
- ❌ 难以测试
- ❌ 破坏封装性

## 配置对象

### AppConfig

**文件**: `src/v1/DDD/app/src/main/config/app_config.py`

```python
@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_size: int = 10
    pool_recycle: int = 3600
    echo: bool = False
    
    @property
    def url(self) -> str:
        """动态生成数据库连接URL"""
        return f"mysql+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class HttpConfig:
    timeout: int = 30
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 10
    pool_timeout: int = 10
    max_connections: int = 100
    max_keepalive_connections: int = 20

@dataclass
class NewsSourceConfig:
    module_paths: list[str]

@dataclass
class AppConfig:
    env: str
    log_level: str
    database: DatabaseConfig
    http: HttpConfig
    news_source: NewsSourceConfig
    
    @classmethod
    def from_env(cls, env_file: str = ".env") -> "AppConfig":
        """从 .env 文件加载配置"""
        load_dotenv(env_file)
        
        return cls(
            env=os.getenv("ENV", "dev"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            database=DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                # ... 其他配置
            ),
            http=HttpConfig(
                timeout=int(os.getenv("HTTP_TIMEOUT", "30")),
                # ... 其他配置
            ),
            news_source=NewsSourceConfig(
                module_paths=os.getenv("NEWS_SOURCE_MODULES", "").split(","),
            ),
        )
```

### 配置文件（.env）

```ini
# 环境
ENV=dev

# 日志
LOG_LEVEL=INFO

# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=news_crawl
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_ECHO=false

# HTTP
HTTP_TIMEOUT=30
HTTP_CONNECT_TIMEOUT=10
HTTP_READ_TIMEOUT=30
HTTP_WRITE_TIMEOUT=10
HTTP_POOL_TIMEOUT=10
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE_CONNECTIONS=20

# 新闻源模块
NEWS_SOURCE_MODULES=v1.DDD.app.src.resource.news_source
```

## 使用示例

### 基本使用

```python
# 1. 创建容器
container = AppContainer()

# 2. 获取配置
config = container.config()
print(f"环境: {config.env}")
print(f"数据库: {config.database.url}")

# 3. 获取应用服务
app_service = container.news_crawl_application_service()

# 4. 使用服务
result = await app_service.crawl_single_source("id_jawapos")

# 5. 关闭资源
await container.shutdown_resources()
```

### 与Application集成

```python
# 应用启动
async def create_app() -> Application:
    # 1. 创建容器
    container = AppContainer()
    
    # 2. 加载配置
    config = container.config()
    
    # 3. 配置日志
    logging.basicConfig(level=config.log_level)
    
    # 4. 创建应用
    return Application(container)

# 使用
app = await create_app()
try:
    service = app.container.news_crawl_application_service()
    result = await service.crawl_single_source("id_jawapos")
finally:
    await app.shutdown()
```

### 测试中使用

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_container():
    """创建Mock容器用于测试"""
    container = MagicMock(spec=AppContainer)
    
    # Mock配置
    container.config.return_value = AppConfig(...)
    
    # Mock Repository
    mock_repo = AsyncMock()
    container.news_crawl_repository.return_value = mock_repo
    
    # Mock HTTP Adapter
    mock_http = AsyncMock()
    container.http_adapter.return_value = mock_http
    
    return container

async def test_crawl_service(mock_container):
    """测试爬取服务"""
    service = mock_container.news_crawl_application_service()
    
    # 配置 Mock 行为
    service.crawl_single_source = AsyncMock(return_value=CrawlResultEntity(...))
    
    # 执行测试
    result = await service.crawl_single_source("test_source")
    
    # 验证
    assert result is not None
    service.crawl_single_source.assert_called_once_with("test_source")
```

## 资源管理

### 优雅关闭

容器提供了 `shutdown_resources()` 方法，负责优雅关闭所有资源：

```python
async def shutdown_resources(self):
    """
    优雅关闭所有资源
    
    关闭顺序：
    1. HTTP 连接池（停止新请求）
    2. 数据库引擎（关闭连接池，等待活跃连接结束）
    """
    logger.info("开始关闭应用资源...")
    
    # 1. 关闭 HTTP 连接池
    try:
        http = self.http_adapter()
        if http and hasattr(http, 'close'):
            logger.debug("正在关闭 HTTP 连接池...")
            close_result = http.close()
            # 检查是否是 coroutine
            if asyncio.iscoroutine(close_result):
                await close_result
            logger.info("✓ HTTP 连接池已关闭")
    except Exception as e:
        logger.warning(f"✗ 关闭 HTTP 连接池失败: {e}")
    
    # 2. 关闭数据库引擎（最重要）
    try:
        engine = self.db_engine()
        if engine:
            logger.debug("正在关闭数据库引擎...")
            await engine.dispose()
            logger.info("✓ 数据库引擎已关闭")
    except Exception as e:
        logger.error(f"✗ 关闭数据库引擎失败: {e}")
    
    logger.info("应用资源关闭完成")
```

### 关闭顺序

**重要性**：
1. **HTTP连接池**：先关闭，避免新的HTTP请求
2. **数据库引擎**：最重要，确保所有事务完成

### 错误处理

- ✅ 每个资源独立捕获异常
- ✅ HTTP关闭失败只警告，不中断流程
- ✅ 数据库关闭失败记录错误，但继续
- ✅ 确保所有资源都尝试关闭

## 扩展容器

### 添加新依赖

**步骤**：

1. **在配置中添加新配置项**：
```python
@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0

@dataclass
class AppConfig:
    # ... 其他配置
    redis: RedisConfig
```

2. **在容器中注册**：
```python
class AppContainer(containers.DeclarativeContainer):
    # ... 其他依赖
    
    # Redis客户端（单例）
    redis_client = providers.Singleton(
        create_redis_client,
        host=config.provided.redis.host,
        port=config.provided.redis.port,
        db=config.provided.redis.db,
    )
```

3. **注入到服务**：
```python
news_crawl_application_service = providers.Factory(
    NewsCrawlApplicationService,
    repository=news_crawl_repository,
    http_adapter=http_adapter,
    redis_client=redis_client,  # 新依赖
    # ... 其他依赖
)
```

4. **更新关闭逻辑**：
```python
async def shutdown_resources(self):
    # ... 关闭HTTP和数据库
    
    # 3. 关闭 Redis
    try:
        redis = self.redis_client()
        if redis:
            await redis.close()
            logger.info("✓ Redis 连接已关闭")
    except Exception as e:
        logger.warning(f"✗ 关闭 Redis 失败: {e}")
```

### 替换实现

**场景**：测试时替换真实实现为Mock

```python
# 创建测试容器
test_container = AppContainer()

# 替换 Repository 实现
test_container.news_crawl_repository.override(
    providers.Singleton(MockRepository)
)

# 替换 HTTP 适配器
test_container.http_adapter.override(
    providers.Singleton(MockHttpAdapter)
)

# 使用测试容器
service = test_container.news_crawl_application_service()
```

## 最佳实践

### ✅ DO

1. **配置驱动**：所有配置都从 `.env` 读取
2. **单例复用**：全局资源使用单例（连接池）
3. **工厂隔离**：有状态服务使用工厂
4. **构造器注入**：依赖通过构造器注入
5. **优雅关闭**：总是调用 `shutdown_resources()`
6. **类型提示**：使用类型提示提高可读性

### ❌ DON'T

1. **避免容器注入**：不要直接传入容器
2. **避免循环依赖**：设计时避免A依赖B，B依赖A
3. **避免硬编码配置**：所有配置都应从 `.env` 读取
4. **避免在容器中包含业务逻辑**：容器只负责依赖管理
5. **避免忘记关闭资源**：可能导致连接泄漏

## 相关记忆

- **应用层概览** → `04-application/README`
- **触发器系统** → `04-application/trigger_system`
- **生命周期管理** → `04-application/lifecycle`
- **应用配置** → `04-application/config`