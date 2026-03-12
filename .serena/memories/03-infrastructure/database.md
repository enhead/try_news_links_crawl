# 数据库设计

> MySQL 表结构和设计原则

## 核心表

### 1. news_source（新闻源元数据）
**职责**：存储新闻源静态配置

**关键字段**：
- `resource_id` - 唯一标识（如 "sg_straits_times"）
- `name` - 新闻源名称
- `domain` - 域名
- `url` - 主页 URL
- `country` - 国家代码
- `language` - 语言代码
- `status` - 状态（0=正常, 1=禁用, 2=异常）

**索引**：
- 主键：`id`
- 唯一索引：`resource_id`
- 普通索引：`domain`, `status`, `country`

### 2. news_link（新闻链接）
**职责**：记录爬取的新闻链接和处理状态

**关键字段**：
- `url` - 新闻链接（唯一）
- `resource_id` - 关联 news_source
- `category` - 栏目分类
- `crawl_params` - JSON，记录爬取参数
- `is_parse` - 解析状态
- `is_translated` - 翻译状态
- `success` - 同步状态

**冗余字段**（避免 JOIN）：
- `country`, `name`, `domain`, `language`

**索引**：
- 主键：`id`
- 唯一索引：`url`
- 普通索引：`resource_id`, `is_parse`, `country`

### 3. news_source_health_check（健康检查）
**职责**：记录健康检查历史

**关键字段**：
- `resource_id` - 新闻源标识
- `check_status` - 检查状态（0=成功, 1=HTTP错误, 2=解析错误, 3=空结果）
- `checked_at` - 检查时间
- `links_found` - 发现的链接数
- `http_status_code` - HTTP 状态码（可选）
- `error_message` - 错误详情（可选）

**索引**：
- 主键：`id`
- 外键：`resource_id` → `news_source.resource_id`
- 普通索引：`checked_at`

## 设计原则

### 冗余存储
- 避免频繁 JOIN 操作
- 提升查询性能

### JSON 字段
- 存储调试信息（crawl_params）
- 灵活扩展

### 流水线状态
- 多阶段处理状态字段
- 支持增量处理

## SQL 脚本
**位置**：`doc/sql/news_crawl.sql`

## 相关链接

- [DAO 层](dao) - 数据访问实现
- [Repository](repository) - 仓储实现
- [元数据设计](../02-domain/config/metadata) - NewsSourceMetadata
