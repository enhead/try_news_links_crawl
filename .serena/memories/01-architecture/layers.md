# 4 层架构说明

## 架构图

```
┌──────────────────────────────────┐
│   Application 层                  │  ← 应用启动、配置、依赖注入容器
├──────────────────────────────────┤
│   API / Trigger 层（待实现）      │  ← 接口实现、定时任务、消息接收
├──────────────────────────────────┤
│   Domain 层                       │  ← 领域模型、领域服务、仓储接口
├──────────────────────────────────┤
│   Infrastructure 层               │  ← 仓储实现、数据库、HTTP
└──────────────────────────────────┘
```

## 各层职责

### Domain 层（核心）
**职责**：
- 领域模型定义（Entity、ValueObject、Aggregate）
- 领域服务（业务逻辑）
- 仓储接口定义（不实现）

**原则**：
- 不依赖任何外部框架
- 纯业务逻辑
- 定义抽象接口

**核心目录**：
- `model/` - 领域模型
- `service/` - 领域服务
- `repository/` - 仓储接口

**示例**：
- `INewsLinkCrawlService` - 爬虫领域服务接口
- `INewsCrawlRepository` - 数据访问接口
- `AbstractNewsSourceConfig` - 新闻源配置抽象

### Infrastructure 层（技术实现）
**职责**：
- 实现 Domain 层定义的接口
- 数据库访问（DAO、ORM）
- HTTP 客户端封装
- 外部服务集成

**原则**：
- 依赖 Domain 层接口
- 提供具体技术实现
- 不包含业务逻辑

**核心目录**：
- `persistent/` - 持久化实现
- `http/` - HTTP 适配器
- `config/` - 技术配置

**示例**：
- `NewsLinksCrawlRepository` - 仓储实现
- `HttpAdapter` - HTTP 客户端封装
- `NewsSourceDAO` - 数据访问对象

### Application 层（应用启动）
**职责**：
- 应用启动和配置
- 依赖注入容器（AppContainer）
- AOP 切面、生命周期管理
- 打包和部署配置

**原则**：
- 专门为启动服务而存在
- 管理依赖关系
- 不包含业务逻辑

**核心目录**：
- `main/` - 应用启动基础设施
- `config/` - 配置文件
- `DI/` - 依赖注入定义

**示例**：
- `AppContainer` - 依赖注入容器（提供服务实例）
- `Application` - 应用入口
- `DatabaseConfig` - 数据库配置

### API / Trigger 层（待实现）
**职责**：
- 接口实现（REST API）
- 定时任务触发（Cron）
- 消息队列消费（MQ）
- 适配外部请求到领域服务

**原则**：
- 依赖 Domain 层服务
- 处理请求/响应转换
- 不包含业务逻辑

**说明**：
- 也叫 trigger 触发器层或 adapter 适配器层
- 小项目可以直接调用 Domain 层（无需 case 编排层）

## 依赖关系

```
Application 层（启动）
    ↓
API/Trigger 层 → Domain 层 ← Infrastructure 层
              （调用）    （实现接口）
```

**依赖规则**：
1. Application 层在最外层（负责启动和配置）
2. API/Trigger 层依赖 Domain 层（小项目直接调用领域服务）
3. Domain 层不依赖任何层（定义仓储接口）
4. Infrastructure 层依赖 Domain 层（实现仓储接口，依赖倒置）

## 跨层交互示例

### 启动流程
```python
# 1. Application 层 - 启动应用
class Application:
    def __init__(self):
        self.container = AppContainer()  # 依赖注入容器
        self.container.config.from_yaml('config.yaml')
        self.container.wire(modules=[...])
    
    async def start(self):
        await self.container.db().connect()

# 2. AppContainer - 提供服务实例
class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    db = providers.Singleton(Database, config=config.database)
    repository = providers.Factory(NewsLinksCrawlRepository, db=db)
    crawl_service = providers.Factory(NewsLinkCrawlService, repository=repository)
```

### 爬取流程（待实现）
```python
# 1. API/Trigger 层 - 接收请求
@app.post("/crawl/{resource_id}")
async def crawl_endpoint(resource_id: str):
    # 从容器获取服务
    service = app.container.crawl_service()
    return await service.execute_crawl(resource_id)

# 2. Domain 层 - 执行业务逻辑
class NewsLinkCrawlService:
    def __init__(self, repository: INewsCrawlRepository):
        self.repository = repository  # 依赖接口，不依赖具体实现
    
    async def execute_crawl(self, resource_id: str):
        # 构建 Layer 树
        # 执行爬取
        # 调用仓储保存
        await self.repository.save_batch(aggregate)

# 3. Infrastructure 层 - 实现仓储接口
class NewsLinksCrawlRepository(INewsCrawlRepository):
    async def save_batch(self, aggregate):
        # 保存到数据库
        ...
```

## 分层优势

### 启动与业务分离
Application 层专注启动配置，Domain 层专注业务逻辑

### 依赖倒置
Infrastructure 层依赖 Domain 层接口，而非相反

### 业务逻辑独立
Domain 层不依赖框架，易于测试和迁移

### 技术实现可替换
Infrastructure 层可替换（如切换数据库），不影响业务逻辑

### 小项目简化
无 case 编排层，API/Trigger 层直接调用 Domain 层，降低维护成本
