# 架构决策记录（ADR）

> Architecture Decision Records - 记录重要的架构决策

## 决策索引

1. [NewsSourceMetadata 实体设计](#1-newssourcemetadata-实体设计)
2. [AbstractNewsSourceConfig 重构](#2-abstractnewssourceconfig-重构)
3. [Repository 接口重构](#3-repository-接口重构)
4. [服务模块重组](#4-服务模块重组)
5. [应用启动基础设施](#5-应用启动基础设施)
6. [健康检查功能设计](#6-健康检查功能设计)
7. [NewsSourceConfigRegistry 注册表](#7-newssourceconfigregistry-注册表)

---

## 1. NewsSourceMetadata 实体设计

**日期**：2026-03-09

**背景**：需要封装新闻源的元数据信息，支持从数据库和 JSON 配置文件加载。

**决策**：
创建 `NewsSourceMetadata` 不可变值对象：
- 与 `news_source` 数据库表结构严格对应
- 使用 `@dataclass(frozen=True)` 保证不可变性
- 包含字段：resource_id, name, domain, url, country, language, status

**位置**：`domain/model/entity/news_source_metadata.py`

**影响**：
- AbstractNewsSourceConfig 需要重构，使用 NewsSourceMetadata 替代散开的字段
- Repository 实现需要使用 NewsSourceMetadata 构建数据
- 需要实现工厂类支持从数据库/JSON 加载

---

## 2. AbstractNewsSourceConfig 重构

**日期**：2026-03-09

**变更内容**：
1. **集成 NewsSourceMetadata**：`__init__` 参数从 `source_id: str` 改为 `metadata: NewsSourceMetadata`
2. **添加便捷属性**：通过 `@property` 向后兼容（如 `source_id` → `metadata.resource_id`）
3. **添加 extract_category() 抽象方法**：由子类实现，从爬取参数中提取栏目分类

**向后兼容性**：通过 `@property` 提供便捷属性，现有代码使用 `config.source_id` 无需修改。

**影响**：
- 需要实现工厂类从数据库/JSON 加载 NewsSourceMetadata 并构建配置对象
- 具体新闻源配置子类需要实现 extract_category() 方法

---

## 3. Repository 接口重构

**日期**：2026-03-09

**背景**：原有两个独立接口（INewsSourceRepository 和 INewsLinksCrawlRepository）职责相关，且命名不够清晰。

**决策**：
合并为统一的 `INewsCrawlRepository` 接口：
- **新闻源元数据查询**：`get_source_by_resource_id()`, `get_all_active_sources()`, `get_all_sources()`
- **新闻链接去重和保存**：`check_exists_batch()`, `save_batch()`

**优点**：
- 命名更清晰，见名知意
- 职责统一，都是爬虫系统的数据访问
- 减少接口碎片化

**位置**：`domain/repository/base_news_links_crawl_repository.py`

---

## 4. 服务模块重组

**日期**：2026-03-10

**背景**：原来的服务模块组织混乱，`crawl_layer`、`config`、`impl` 分散在不同位置。

**决策**：
将所有单个新闻源爬取相关的服务统一到 `single_news_link_crawl/` 目录：
```
service/
├── single_news_link_crawl/      # 单源爬取服务
│   ├── base_news_link_crawl_service.py
│   ├── impl/
│   ├── crawl_layer/
│   └── news_source_health_check/
└── config/                      # 配置管理
```

**优点**：
- 职责清晰：单源爬取相关的所有服务在一个目录
- 易于理解：新开发者能快速找到相关代码
- 便于扩展：未来添加多源调度服务时，可以创建 `multi_news_link_crawl/` 目录

---

## 5. 应用启动基础设施

**日期**：2026-03-10

**背景**：需要完整的应用启动和生命周期管理机制，包括依赖注入、配置管理和资源管理。

**决策**：
1. **依赖注入容器（AppContainer）**：使用 `dependency-injector` 框架
   - 单例管理：配置、数据库引擎、HTTP 适配器
   - 工厂管理：Session、DAO、Repository、ApplicationService

2. **配置管理（AppConfig）**：使用 `dataclass` + `python-dotenv`
   - 从 `.env` 文件加载
   - 类型安全（类型注解 + 验证）

3. **应用入口（Application）**：
   - `Application` 类持有容器，管理生命周期
   - `create_app()` 工厂函数创建应用实例
   - `shutdown()` 方法优雅关闭

**位置**：`app/src/main/`

**优点**：
- 依赖管理清晰
- 生命周期可控
- 资源管理安全
- 易于测试

---

## 6. 健康检查功能设计

**日期**：2026-03-10

**背景**：需要定期检查新闻源的可用性，自动标记异常源。

**决策**：
1. **数据模型**：
   - `HealthCheckRecordEntity` - 记录单次健康检查结果
   - `HealthCheckStatusVO` - 健康检查状态枚举

2. **服务接口**：
   - `INewsSourceHealthCheckService` - 健康检查服务接口
   - 流程：构建测试参数 → 发送请求 → 解析响应 → 保存记录 → 更新源状态

3. **数据库表**：`news_source_health_check`

**设计原则**：
- **复用现有能力**：健康检查复用 `parse_response()` 方法
- **独立记录**：健康检查发现的链接不保存到 `news_link` 表
- **自动标记**：连续失败 3 次后自动标记为异常（`status=2`）

**位置**：`domain/service/single_news_link_crawl/news_source_health_check/`

---

## 7. NewsSourceConfigRegistry 注册表

**日期**：2026-03-10

**背景**：需要一个机制来管理多个新闻源配置类，支持动态注册和按需加载。

**决策**：
实现两层能力：
1. **纯注册表**：装饰器注册 + 类查找（无副作用）
2. **单例工厂**：`create_config()` 负责查 DB、实例化、缓存

**核心方法**：
- `register(resource_id)` - 装饰器，注册配置类
- `get_config_class(resource_id)` - 获取配置类（不实例化）
- `create_config(resource_id, repository)` - 获取配置实例（单例）
- `clear_cache(resource_id)` - 清除实例缓存（测试用）

**位置**：`domain/service/config/news_resource/registry/news_source_config_registry.py`

**优点**：
- 装饰器注册：简洁优雅，自动注册
- 单例缓存：避免重复查询数据库
- 按需加载：首次使用时才查询数据库
- 类型安全：编译时检查是否继承 AbstractNewsSourceConfig

**注意事项**：
- 配置类必须在应用启动时导入，否则装饰器不会执行
- 建议在 `app/src/resource/news_source/__init__.py` 中统一导入

---

## 设计原则总结

### 依赖倒置原则（DIP）
- Domain 层定义接口，Infrastructure 层实现接口
- 高层模块不依赖低层模块，都依赖抽象

### 单一职责原则（SRP）
- 每个类只有一个职责
- 每个服务目录只包含相关功能

### 开闭原则（OCP）
- 使用工厂和注册表支持扩展
- 通过装饰器添加新功能，无需修改现有代码

### 配置驱动
- 所有配置从 .env 文件加载
- 支持多环境配置
- 配置类型安全

### 资源管理
- 单例复用（数据库连接池、HTTP 连接池）
- 工厂按需创建（Session、DAO、Repository）
- 优雅关闭（自动释放资源）
