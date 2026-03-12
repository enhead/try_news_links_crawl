# 🎯 领域层导航

> 核心业务逻辑和领域模型

## 子领域

### [crawler/](crawler/README) - 爬虫领域 ⭐
多层级爬取系统的核心实现
- 三种层类型（枚举/映射/顺序）
- 爬取节点
- 智能剪枝机制

### [config/](config/README) - 配置管理
新闻源配置体系
- 抽象配置类
- 注册表机制
- 元数据管理

### [health_check/](health_check/README) - 健康检查
新闻源可用性监控
- 健康检查服务
- 检查记录实体
- 状态枚举

## 阅读路径

### 理解爬虫机制
```
1. crawler/README → 爬虫概览
2. crawler/layers → 三种层类型
3. crawler/nodes → 爬取节点
4. crawler/execution_flow → 执行流程
```

### 实现新闻源配置
```
1. config/README → 配置管理概览
2. config/abstract_config → AbstractNewsSourceConfig
3. config/registry → 注册表机制
4. config/metadata → 元数据设计
```

### 调试健康检查
```
1. health_check/README → 功能概览
2. health_check/service → 服务接口
3. health_check/entity → 实体设计
```

## 领域模型

### Entity（实体）
- `NewsSourceMetadata` - 新闻源元数据
- `HealthCheckRecordEntity` - 健康检查记录
- `CrawlResultEntity` - 爬取结果

### Value Object（值对象）
- `HealthCheckStatusVO` - 健康检查状态
- `NewsSourceStatusVO` - 新闻源状态
- `ResponseParseResultStatusVO` - 响应解析状态

### Aggregate（聚合）
- `NewsLinkBatchAggregate` - 新闻链接批次聚合

## 领域服务

### 爬虫服务
- `INewsLinkCrawlService` - 爬取领域服务接口
- `NewsLinkCrawlService` - 爬取服务实现

### 健康检查服务
- `INewsSourceHealthCheckService` - 健康检查服务接口

## 仓储接口

- `INewsCrawlRepository` - 统一仓储接口
  - 新闻源元数据查询
  - 新闻链接去重和保存
