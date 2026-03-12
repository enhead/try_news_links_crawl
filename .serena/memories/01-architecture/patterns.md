# 设计模式总览

## 工厂模式（Factory Pattern）

### CrawlLayerFactory（层工厂）
**位置**：`domain/service/single_news_link_crawl/crawl_layer/factory/layer_factory.py`

**用途**：根据 LayerType 创建对应的层实例

**实现方式**：
```python
@CrawlLayerFactory.register(LayerType.SEQUENTIAL)
class SequentialLayer(AbstractCrawlLayer):
    ...

# 使用工厂创建层
layer = CrawlLayerFactory.build(schema, next_layer, context)
```

**优点**：
- 装饰器注册，自动发现
- 支持动态扩展新层类型
- 统一创建接口

### NewsSourceConfigFactory（配置元数据工厂）
**位置**：`domain/service/config/news_resource/factory/news_source_config_factory.py`

**用途**：从多种来源加载新闻源元数据

**方法**：
- `load_metadata_from_repository()` - 从数据库加载
- `load_metadata_from_json()` - 从 JSON 文件加载
- `load_metadata_from_dict()` - 从字典构造

**优点**：
- 支持多种数据源
- 完善的字段验证
- 依赖接口而非具体实现

## 注册表模式（Registry Pattern）

### NewsSourceConfigRegistry（配置注册表）
**位置**：`domain/service/config/news_resource/registry/news_source_config_registry.py`

**用途**：管理新闻源配置类的注册和实例化

**实现方式**：
```python
@NewsSourceConfigRegistry.register("sg_straits_times")
class StraitTimesConfig(AbstractNewsSourceConfig):
    ...

# 获取单例实例
config = await NewsSourceConfigRegistry.create_config("sg_straits_times", repo)
```

**两层能力**：
1. **纯注册表**：装饰器注册 + 类查找
2. **单例工厂**：首次查 DB，后续走缓存

**优点**：
- 装饰器注册，简洁优雅
- 单例缓存，避免重复查询
- 按需加载，首次使用才查询

## 仓储模式（Repository Pattern）

### INewsCrawlRepository（仓储接口）
**位置**：`domain/repository/base_news_links_crawl_repository.py`

**用途**：抽象数据访问逻辑

**实现**：`NewsLinksCrawlRepository`（Infrastructure 层）

**优点**：
- 业务逻辑不依赖具体数据库
- 易于切换数据源
- 易于 mock 测试

## 适配器模式（Adapter Pattern）

### HttpAdapter
**位置**：`infrastructure/http/httpx_adapter.py`

**用途**：封装 httpx 客户端，提供统一接口

**优点**：
- 屏蔽底层 HTTP 库细节
- 易于切换 HTTP 库（如换成 aiohttp）
- 统一错误处理

## 依赖注入模式（Dependency Injection）

### AppContainer
**位置**：`app/src/main/DI/container.py`

**用途**：管理对象依赖和生命周期

**技术**：`dependency-injector` 框架

**管理策略**：
- **单例**：配置、数据库引擎、HTTP 适配器
- **工厂**：Session、DAO、Repository、ApplicationService

**优点**：
- 依赖关系清晰
- 生命周期可控
- 易于测试（可注入 mock）

## 模板方法模式（Template Method）

### AbstractNewsSourceConfig
**位置**：`domain/service/config/news_resource/abstract_news_source_config.py`

**模板方法**：
- `build_request()` - 构建请求（抽象）
- `parse_response()` - 解析响应（抽象）
- `extract_category()` - 提取分类（抽象）

**子类实现**：
每个新闻源实现具体的解析逻辑

**优点**：
- 定义统一流程
- 子类只需实现特定步骤
- 易于扩展新闻源

### AbstractCrawlLayer
**位置**：`domain/service/single_news_link_crawl/crawl_layer/abstract_layer.py`

**模板方法**：
- `execute()` - 执行爬取（模板）
- `_generate_params()` - 生成参数（抽象）

**优点**：
- 统一爬取流程
- 各层实现自己的参数生成逻辑

## 策略模式（Strategy Pattern）

### 爬取节点（CrawlNode）
不同节点实现不同的爬取策略：
- `DefaultCrawlNode` - 标准爬取流程

未来可扩展：
- `CacheCrawlNode` - 带缓存的爬取
- `RateLimitCrawlNode` - 带限流的爬取

## 组合模式（Composite Pattern）

### Layer 树结构
层可以嵌套形成树状结构：
```
EnumerableLayer (栏目)
  └─ MappingLayer (子栏目)
      └─ SequentialLayer (翻页)
```

**优点**：
- 支持复杂的多维度遍历
- 统一的 `execute()` 接口
- 灵活组合

## 不可变对象模式（Immutable Object）

### NewsSourceMetadata
**位置**：`domain/model/entity/news_source_metadata.py`

**实现**：
```python
@dataclass(frozen=True)
class NewsSourceMetadata:
    resource_id: str
    name: str
    ...
```

**优点**：
- 线程安全
- 避免意外修改
- 可作为字典键

## 观察者模式（未实现，规划中）

### 健康检查通知
未来可实现：
- 健康检查失败时发送通知
- 支持多种通知方式（邮件、钉钉、Slack）

## 设计模式应用总结

| 模式 | 应用场景 | 核心价值 |
|------|---------|---------|
| 工厂模式 | 层创建、配置加载 | 统一创建接口，支持扩展 |
| 注册表模式 | 配置管理 | 装饰器注册，自动发现 |
| 仓储模式 | 数据访问 | 抽象数据源，易于测试 |
| 适配器模式 | HTTP 封装 | 屏蔽底层细节 |
| 依赖注入 | 对象管理 | 解耦依赖，生命周期管理 |
| 模板方法 | 爬取流程 | 定义骨架，子类实现细节 |
| 策略模式 | 爬取节点 | 可替换的算法实现 |
| 组合模式 | 层树结构 | 统一接口，灵活组合 |
