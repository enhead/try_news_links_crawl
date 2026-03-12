# 应用层概览

**最后更新**: 2026-03-11

## 职责

应用层是系统的编排层，负责：

1. **应用启动与关闭**：管理应用生命周期
2. **依赖注入**：统一管理和注入所有依赖
3. **服务编排**：协调领域服务完成业务用例
4. **触发器集成**：支持多种触发方式（CLI、API、定时任务）
5. **配置管理**：统一管理应用配置
6. **事务管理**：控制数据库事务边界
7. **错误处理**：统一的异常处理和日志记录

## 核心组件

### 1. DI容器（`DI/container.py`）

**类型**: `AppContainer`

**职责**：
- 管理所有依赖的创建和生命周期
- 单例管理：配置、数据库引擎、HTTP适配器
- 工厂管理：Session、DAO、Repository、Service
- 提供优雅关闭资源的接口

**依赖树**：
```
AppConfig (单例)
  ├─ DatabaseConfig
  ├─ HttpConfig
  └─ NewsSourceConfig

基础设施（单例）：
  ├─ DbEngine (AsyncEngine)
  ├─ DbSessionFactory (async_sessionmaker)
  └─ HttpAdapter (httpx客户端)

持久化层（单例/工厂）：
  └─ NewsLinksCrawlRepository (单例)

领域层（工厂）：
  └─ NewsLinkCrawlService

应用层（工厂）：
  └─ NewsCrawlApplicationService
```

**使用示例**：
```python
# 创建容器
container = AppContainer()

# 获取应用服务
app_service = container.news_crawl_application_service()

# 执行业务逻辑
result = await app_service.crawl_single_source("id_jawapos")

# 关闭资源
await container.shutdown_resources()
```

### 2. 应用配置（`config/app_config.py`）

**类型**: `AppConfig`

**职责**：
- 从 `.env` 文件加载配置
- 提供配置对象（DatabaseConfig、HttpConfig、NewsSourceConfig）
- 验证配置有效性

**配置项**：
- `env`: 环境（dev/prod）
- `log_level`: 日志级别
- `database`: 数据库配置
- `http`: HTTP客户端配置
- `news_source`: 新闻源模块路径

### 3. 应用启动（`application.py`）

**类型**: `Application`

**职责**：
- 初始化 DI 容器
- 配置日志系统
- 管理应用生命周期
- 提供应用关闭接口

**生命周期**：
```
1. create_app()
   ├─ 创建 DI 容器
   ├─ 加载配置
   ├─ 配置日志
   └─ 返回 Application 实例

2. 运行业务逻辑
   └─ 通过 container 获取服务

3. app.shutdown()
   ├─ 关闭 HTTP 连接池
   ├─ 关闭数据库引擎
   └─ 释放所有资源
```

### 4. CLI主程序（`main.py`）

**类型**: `main()` 函数 + `NewscrawlApplication` 类

**职责**：
- 解析命令行参数
- 配置日志级别
- 创建并运行应用
- 错误处理和优雅退出

**命令行参数**：
- `--source, -s`: 指定新闻源（逗号分隔）
- `--list-sources, -l`: 列出所有新闻源
- `--log-level`: 设置日志级别（DEBUG/INFO/WARNING/ERROR）

**使用示例**：
```bash
# 爬取所有新闻源
python -m v1.DDD.app.src.main.main

# 爬取指定新闻源
python -m v1.DDD.app.src.main.main --source id_jawapos

# 列出所有新闻源
python -m v1.DDD.app.src.main.main --list-sources

# 调整日志级别
python -m v1.DDD.app.src.main.main --log-level DEBUG
```

### 5. 应用服务（`domain/service/impl/news_crawl_application_service.py`）

**类型**: `NewsCrawlApplicationService`

**职责**：
- 加载新闻源配置（`load_all_source_configs`）
- 爬取单个新闻源（`crawl_single_source`）
- 爬取多个新闻源（`crawl_multiple_sources`）
- 协调领域服务和基础设施
- 事务管理（通过Repository）

**依赖**：
- `repository`: 数据持久化
- `http_adapter`: HTTP请求
- `crawl_service`: 爬取业务逻辑
- `news_source_config`: 新闻源配置

**核心方法**：
```python
class NewsCrawlApplicationService:
    async def load_all_source_configs(
        self,
        module_paths: Optional[str | list[str]] = None
    ) -> list[str]:
        """加载所有新闻源配置"""
        
    async def crawl_single_source(
        self,
        resource_id: str
    ) -> CrawlResultEntity:
        """爬取单个新闻源"""
        
    async def crawl_multiple_sources(
        self,
        resource_ids: list[str]
    ) -> list[CrawlResultEntity]:
        """批量爬取多个新闻源"""
```

## 应用流程

### 完整启动流程

```
1. main()
   ↓
2. 解析命令行参数
   ↓
3. create_app()
   ├─ 创建 AppContainer
   ├─ 加载 AppConfig
   ├─ 配置日志
   └─ 返回 Application
   ↓
4. 创建触发器（ManualTrigger）
   ├─ 传入 container
   └─ 传入 source_ids
   ↓
5. trigger.run()
   ├─ trigger.setup()
   │  └─ app_service.load_all_source_configs()
   ├─ trigger.start()
   │  └─ app_service.crawl_multiple_sources()
   └─ trigger.stop()
   ↓
6. app.shutdown()
   ├─ http_adapter.close()
   └─ db_engine.dispose()
```

### 爬取单个新闻源流程

```
1. app_service.crawl_single_source(resource_id)
   ↓
2. 从注册表获取配置
   ├─ NewsSourceConfigRegistry.get(resource_id)
   └─ 抛出 KeyError 如果未注册
   ↓
3. 从数据库加载元数据
   ├─ repository.get_news_source_metadata(resource_id)
   └─ 抛出 ValueError 如果不存在
   ↓
4. 构建爬取因子
   ├─ NewsResourceCrawlFactorEntity
   ├─ 包含配置 + 元数据 + HTTP适配器
   └─ 设置为激活状态
   ↓
5. 调用领域服务
   ├─ crawl_service.crawl(factor)
   └─ 执行多层爬取逻辑
   ↓
6. 持久化结果
   ├─ repository.save_crawl_result(result)
   ├─ 保存新链接
   └─ 保存爬取日志
   ↓
7. 返回爬取结果
```

## 关键设计

### 1. 依赖注入模式

**优势**：
- ✅ 解耦：各层独立，易于测试
- ✅ 单例管理：连接池复用，节省资源
- ✅ 工厂模式：按需创建，避免浪费
- ✅ 生命周期管理：统一关闭资源

**实现**：
```python
# 单例（全局唯一，复用资源）
config = providers.Singleton(AppConfig.from_env)
db_engine = providers.Singleton(create_async_engine, ...)
http_adapter = providers.Singleton(HttpAdapter, ...)

# 工厂（每次创建新实例）
news_link_crawl_service = providers.Factory(NewsLinkCrawlService)
news_crawl_application_service = providers.Factory(
    NewsCrawlApplicationService,
    repository=news_crawl_repository,
    http_adapter=http_adapter,
    ...
)
```

### 2. 触发器模式

**优势**：
- ✅ 解耦触发方式和业务逻辑
- ✅ 统一的生命周期管理（setup/start/stop）
- ✅ 易于扩展新的触发方式
- ✅ 便于测试和调试

**实现**：
- `BaseTrigger`: 抽象基类
- `ManualTrigger`: 命令行触发
- `APITrigger`: HTTP API触发（待启用）
- `SchedulerTrigger`: 定时任务触发（待启用）

### 3. 应用服务模式

**职责边界**：
- ❌ 不处理HTTP请求和响应（由触发器处理）
- ❌ 不包含业务逻辑（由领域服务处理）
- ✅ 只负责编排和协调
- ✅ 管理事务边界
- ✅ 转换数据格式

**示例**：
```python
# ✅ 正确：应用服务只编排
async def crawl_single_source(self, resource_id: str):
    config = self._get_config(resource_id)
    metadata = await self._load_metadata(resource_id)
    factor = self._build_factor(config, metadata)
    result = await self.crawl_service.crawl(factor)
    await self.repository.save(result)
    return result

# ❌ 错误：应用服务不应包含业务逻辑
async def crawl_single_source(self, resource_id: str):
    # 这些应该在领域层
    response = await self.http.get(url)
    links = self._parse_html(response)
    filtered_links = self._filter_links(links)
    ...
```

## 配置管理

### 配置文件（`.env`）

```ini
# 环境
ENV=dev

# 日志
LOG_LEVEL=INFO

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=news_crawl
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_ECHO=false

# HTTP配置
HTTP_TIMEOUT=30
HTTP_CONNECT_TIMEOUT=10
HTTP_READ_TIMEOUT=30
HTTP_WRITE_TIMEOUT=10
HTTP_POOL_TIMEOUT=10
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE_CONNECTIONS=20

# 新闻源配置模块
NEWS_SOURCE_MODULES=v1.DDD.app.src.resource.news_source
```

### 配置对象结构

```python
AppConfig
  ├─ env: str
  ├─ log_level: str
  ├─ database: DatabaseConfig
  │    ├─ host, port, user, password, database
  │    ├─ pool_size, pool_recycle
  │    └─ url (动态生成)
  ├─ http: HttpConfig
  │    ├─ timeout, connect_timeout, ...
  │    └─ max_connections, ...
  └─ news_source: NewsSourceConfig
       └─ module_paths: list[str]
```

## 错误处理

### 分层错误处理策略

```
触发层：
  ├─ 捕获所有异常
  ├─ 记录详细日志
  ├─ 返回友好错误信息
  └─ HTTP状态码（如果是API触发）

应用层：
  ├─ 捕获领域异常
  ├─ 添加上下文信息
  ├─ 记录应用日志
  └─ 向上传播或转换异常

领域层：
  ├─ 抛出领域异常（KeyError、ValueError）
  └─ 不捕获异常（让上层处理）

基础设施层：
  ├─ 捕获技术异常（网络、数据库）
  └─ 转换为领域异常或向上传播
```

### 常见错误处理

```python
# KeyError: 新闻源未注册
try:
    result = await app_service.crawl_single_source("unknown_source")
except KeyError:
    logger.error("新闻源未注册")

# ValueError: 数据库中不存在
try:
    result = await app_service.crawl_single_source("id_jawapos")
except ValueError:
    logger.error("数据库中未找到该新闻源")

# Exception: 其他错误（网络、解析等）
try:
    result = await app_service.crawl_single_source("id_jawapos")
except Exception as e:
    logger.error(f"爬取失败: {type(e).__name__}: {e}")
```

## 扩展点

### 1. 添加新的触发方式

位置：`trigger/`

步骤：
1. 继承 `BaseTrigger`
2. 实现 `setup()`, `start()`, `stop()`
3. 在 `main.py` 或独立脚本中使用

### 2. 添加新的应用服务

位置：`domain/service/impl/`

步骤：
1. 在领域层定义服务接口
2. 实现应用服务类
3. 在 `container.py` 中注册
4. 在触发器中使用

### 3. 修改配置

位置：`config/app_config.py`

步骤：
1. 在 `.env.example` 添加配置项
2. 在 `AppConfig` 中添加字段
3. 在容器中使用新配置

## 测试建议

### 单元测试

```python
# 测试应用服务（Mock依赖）
@pytest.fixture
def mock_container():
    container = MagicMock(spec=AppContainer)
    # Mock各种依赖
    return container

async def test_crawl_single_source(mock_container):
    app_service = mock_container.news_crawl_application_service()
    result = await app_service.crawl_single_source("test_source")
    assert result is not None
```

### 集成测试

```python
# 测试完整流程（使用真实容器）
async def test_integration():
    app = await create_app()
    try:
        service = app.container.news_crawl_application_service()
        result = await service.crawl_single_source("id_jawapos")
        assert len(result.urls_found) > 0
    finally:
        await app.shutdown()
```

## 相关记忆

- **触发器系统** → `04-application/trigger_system`
- **DI容器详解** → `04-application/di_container`
- **生命周期管理** → `04-application/lifecycle`
- **配置管理** → `04-application/config`