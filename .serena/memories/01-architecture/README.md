# 架构概览

**最后更新**: 2026-03-11

## 架构风格

**DDD（领域驱动设计） + 清洁架构 + 触发器模式**

- **DDD**: 以业务领域为核心，使用聚合、实体、值对象建模
- **清洁架构**: 依赖倒置，核心业务不依赖外部框架和基础设施
- **触发器模式**: 解耦触发方式和业务逻辑，支持多种触发方式

## 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        触发层 (Trigger)                     │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐│
│  │  Manual    │  │   API    │  │ Scheduler  │  │  Queue   ││
│  │  Trigger   │  │ Trigger  │  │  Trigger   │  │ Trigger  ││
│  └─────┬──────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘│
└────────┼──────────────┼──────────────┼───────────────┼──────┘
         │              │              │               │
         └──────────────┴──────────────┴───────────────┘
                                │
                ┌───────────────▼───────────────┐
                │      应用层 (Application)      │
                │  ┌──────────────────────────┐ │
                │  │  DI Container (单例管理)  │ │
                │  │  - AppConfig             │ │
                │  │  - DbEngine              │ │
                │  │  - HttpAdapter           │ │
                │  │  - Repository            │ │
                │  │  - Services              │ │
                │  └──────────────────────────┘ │
                │  ┌──────────────────────────┐ │
                │  │ NewsCrawlApplicationService│ │
                │  │  - 加载新闻源配置         │ │
                │  │  - 编排爬取任务           │ │
                │  │  - 协调领域服务           │ │
                │  └──────────────────────────┘ │
                └────────────┬──────────────────┘
                             │
                ┌────────────▼──────────────┐
                │    领域层 (Domain)         │
                │  ┌─────────────────────┐  │
                │  │ NewsLinkCrawlService│  │
                │  │  - 单个新闻源爬取   │  │
                │  │  - 爬取层编排       │  │
                │  │  - 业务规则         │  │
                │  └─────────────────────┘  │
                │  ┌─────────────────────┐  │
                │  │ 新闻源配置系统       │  │
                │  │  - 注册表           │  │
                │  │  - 抽象配置         │  │
                │  │  - 工厂             │  │
                │  └─────────────────────┘  │
                │  ┌─────────────────────┐  │
                │  │ 爬取层系统          │  │
                │  │  - 顺序层           │  │
                │  │  - 枚举层           │  │
                │  │  - 映射层           │  │
                │  │  - 爬取节点         │  │
                │  └─────────────────────┘  │
                │  ┌─────────────────────┐  │
                │  │ Repository接口      │  │
                │  └─────────────────────┘  │
                └────────────┬──────────────┘
                             │
                ┌────────────▼──────────────┐
                │   基础设施层 (Infra)       │
                │  ┌─────────────────────┐  │
                │  │ HTTP (HttpAdapter)  │  │
                │  │  - httpx异步客户端  │  │
                │  │  - 连接池管理       │  │
                │  └─────────────────────┘  │
                │  ┌─────────────────────┐  │
                │  │ 数据库 (MySQL)      │  │
                │  │  - SQLAlchemy ORM   │  │
                │  │  - 异步Session      │  │
                │  │  - 连接池           │  │
                │  └─────────────────────┘  │
                │  ┌─────────────────────┐  │
                │  │ Repository实现      │  │
                │  │  - DAO层            │  │
                │  │  - Mapper层         │  │
                │  └─────────────────────┘  │
                └───────────────────────────┘
```

## 核心设计原则

### 1. 依赖倒置原则（DIP）
- **领域层**定义接口（Repository、Config）
- **基础设施层**实现接口
- 依赖方向：触发层 → 应用层 → 领域层 ← 基础设施层

### 2. 单一职责原则（SRP）
- **触发层**：只负责触发方式（HTTP、定时、队列）
- **应用层**：编排服务、事务管理、依赖注入
- **领域层**：核心业务逻辑、业务规则
- **基础设施层**：技术实现（HTTP、数据库、文件）

### 3. 开闭原则（OCP）
- 新增新闻源：继承`AbstractNewsSourceConfig`，注册即可
- 新增触发方式：继承`BaseTrigger`，实现即可
- 新增爬取层类型：实现`AbstractLayer`接口

## 关键特性

### ✅ 已实现
1. **DI容器**：使用`dependency-injector`管理所有依赖
2. **触发器模式**：解耦触发方式和业务逻辑
3. **手动触发器**：命令行直接运行
4. **新闻源配置系统**：注册表 + 工厂模式
5. **爬取层系统**：多层级爬取（顺序/枚举/映射）
6. **爬虫日志**：记录爬取过程和结果

### ⚠️ 框架已就绪（需安装依赖）
1. **API触发器**：HTTP REST API（需FastAPI）
2. **定时任务触发器**：定时自动爬取（需APScheduler）

### 📋 待实现
1. **消息队列触发器**：基于MQ的异步触发

## 目录结构（简化版）

```
src/v1/DDD/
├─ trigger/                    # 触发层（新增）
│  ├─ base_trigger.py          # 触发器基类
│  ├─ api_trigger.py           # API触发器
│  └─ scheduler_trigger.py     # 定时任务触发器
│
├─ app/src/main/               # 应用层（新增）
│  ├─ DI/container.py          # DI容器
│  ├─ config/app_config.py     # 应用配置
│  ├─ application.py           # 应用启动入口
│  └─ main.py                  # CLI主程序
│
├─ domain/                     # 领域层
│  └─ http_news_links_crawl/
│     ├─ service/              # 领域服务
│     │  ├─ impl/news_crawl_application_service.py  # 应用服务
│     │  ├─ single_news_link_crawl/  # 爬虫核心
│     │  └─ config/news_resource/     # 新闻源配置
│     ├─ model/                # 领域模型
│     └─ repository/           # 仓储接口
│
└─ infrastructure/             # 基础设施层
   ├─ http/httpx_adapter.py    # HTTP客户端
   ├─ config/mysql/            # 数据库配置
   └─ persistent/              # 持久化
      ├─ dao/                  # 数据访问对象
      ├─ models/               # ORM模型
      └─ repository/           # 仓储实现
```

## 数据流向

### 启动流程
```
1. create_app()
   ↓
2. 初始化 DI 容器
   ↓
3. 加载配置（.env）
   ↓
4. 创建单例资源（DbEngine, HttpAdapter）
   ↓
5. 创建触发器（Manual/API/Scheduler）
   ↓
6. 运行触发器
```

### 爬取流程
```
1. 触发器触发
   ↓
2. NewsCrawlApplicationService.crawl_single_source()
   ↓
3. 加载新闻源配置（注册表 + 工厂）
   ↓
4. NewsLinkCrawlService.crawl()
   ↓
5. 构建爬取层（顺序层 → 枚举层 → 映射层）
   ↓
6. 逐层执行爬取节点
   ↓
7. HTTP请求（HttpAdapter）
   ↓
8. 解析响应（AbstractNewsSourceConfig.parse_response）
   ↓
9. 持久化（Repository → DAO → MySQL）
   ↓
10. 记录爬取日志
   ↓
11. 返回结果
```

## 扩展点

1. **新增新闻源**：
   - 位置：`app/src/resource/news_source/`
   - 步骤：继承`AbstractNewsSourceConfig` + `@register` + 实现解析方法

2. **新增触发方式**：
   - 位置：`trigger/`
   - 步骤：继承`BaseTrigger` + 实现`setup/start/stop`

3. **新增爬取层类型**：
   - 位置：`domain/service/single_news_link_crawl/crawl_layer/impl/`
   - 步骤：继承`AbstractLayer` + 注册工厂

## 技术栈

- **语言**：Python 3.13
- **DI容器**：dependency-injector
- **数据库**：MySQL + SQLAlchemy (async)
- **HTTP客户端**：httpx (async)
- **日志**：Python logging
- **API框架**：FastAPI（待启用）
- **定时任务**：APScheduler（待启用）