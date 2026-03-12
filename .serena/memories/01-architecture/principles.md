# DDD 和 SOLID 原则

## DDD 原则

### 领域驱动设计（Domain-Driven Design）
本项目采用 DDD 架构，核心思想：
- **领域模型为核心**：业务逻辑在 Domain 层
- **分层清晰**：Domain、Infrastructure、Application、API
- **依赖倒置**：高层不依赖低层，都依赖抽象

### 战术设计模式
- **Entity（实体）**：有唯一标识的领域对象
- **Value Object（值对象）**：无标识的不可变对象
- **Aggregate（聚合）**：一组相关实体的根
- **Repository（仓储）**：数据访问的抽象接口
- **Domain Service（领域服务）**：跨实体的业务逻辑
- **Application Layer（应用层）**：应用启动、配置、依赖注入

## SOLID 原则

### S - 单一职责原则（SRP）
- 每个类只有一个职责
- 每个服务目录只包含相关功能
- **示例**：`single_news_link_crawl/` 只负责单源爬取

### O - 开闭原则（OCP）
- 对扩展开放，对修改关闭
- 使用工厂和注册表支持扩展
- **示例**：`@NewsSourceConfigRegistry.register()` 装饰器注册新配置

### L - 里氏替换原则（LSP）
- 子类可以替换父类使用
- **示例**：所有配置类继承 `AbstractNewsSourceConfig`，可互相替换

### I - 接口隔离原则（ISP）
- 接口细粒度，职责单一
- **示例**：`INewsCrawlRepository` 按功能分组方法

### D - 依赖倒置原则（DIP）
- 高层不依赖低层，都依赖抽象
- **示例**：Domain 层定义 `INewsCrawlRepository` 接口，Infrastructure 层实现

## 应用示例

### 依赖倒置示例
```python
# Domain 层：定义接口
class INewsCrawlRepository(ABC):
    async def get_source_by_resource_id(self, resource_id: str): ...

# Domain 层：领域服务依赖接口
class NewsLinkCrawlService:
    def __init__(self, repository: INewsCrawlRepository):
        self.repository = repository  # 依赖接口，不依赖具体实现

# Infrastructure 层：实现接口
class NewsLinksCrawlRepository(INewsCrawlRepository):
    async def get_source_by_resource_id(self, resource_id: str):
        # 具体实现
        ...

# Application 层：提供依赖注入
class AppContainer(containers.DeclarativeContainer):
    repository = providers.Factory(NewsLinksCrawlRepository, ...)
    crawl_service = providers.Factory(NewsLinkCrawlService, repository=repository)
```

### 开闭原则示例
```python
# 添加新闻源配置：无需修改现有代码
@NewsSourceConfigRegistry.register("new_source")
class NewSourceConfig(AbstractNewsSourceConfig):
    ...
```

## 设计决策原则

### 配置驱动
- 所有配置从 `.env` 文件加载
- 支持多环境配置（dev/prod/test）
- 配置类型安全（dataclass + 类型注解）

### 资源管理
- **单例复用**：数据库连接池、HTTP 连接池
- **工厂按需创建**：Session、DAO、Repository
- **优雅关闭**：自动释放资源

### 测试友好
- 使用依赖注入，易于 mock
- 接口抽象，易于替换实现
- 注册表可清理，测试隔离
