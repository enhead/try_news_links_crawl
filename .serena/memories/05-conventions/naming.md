# 命名规范

> 类、函数、变量、文件命名规则

## 基本规则

### 类名
**PascalCase**

```python
✅ AbstractNewsSourceConfig
✅ NewsLinkCrawlService
✅ HealthCheckRecordEntity
❌ abstract_news_source_config
```

### 函数/方法
**snake_case**

```python
✅ build_request()
✅ parse_response()
✅ execute_crawl()
❌ buildRequest()
❌ ParseResponse()
```

### 变量
**snake_case**

```python
✅ resource_id
✅ crawl_result
✅ http_adapter
❌ resourceId
❌ CrawlResult
```

### 常量
**UPPER_SNAKE_CASE**

```python
✅ DEFAULT_TIMEOUT
✅ MAX_RETRY_COUNT
❌ default_timeout
```

### 私有方法/属性
**前缀下划线**

```python
✅ _fetch_and_parse()
✅ _build_layer_tree()
❌ fetch_and_parse()  # 如果是私有方法
```

## 实体命名

### 实体类
**必须以 `Entity` 结尾**

```python
✅ HealthCheckRecordEntity
✅ CrawlResultEntity
✅ LayerFactorEntity
❌ HealthCheckRecord
❌ CrawlResult
```

**例外**：
```python
✅ NewsSourceMetadata  # 特殊命名，本质是实体
```

### 文件名
**与类名对应**

```python
# 类名
HealthCheckRecordEntity

# 文件名
health_check_record_entity.py
```

## 值对象命名

### 枚举类
**以 `VO` 结尾**

```python
✅ NewsSourceStatusVO
✅ HealthCheckStatusVO
❌ NewsSourceStatus
```

### 使用 Status
**统一使用 `Status` 而非 `State`**

```python
✅ NewsSourceStatusVO
❌ NewsSourceStateVO
```

## DAO 命名

### DAO 类
**以 `DAO` 结尾**

```python
✅ NewsLinkDAO
✅ NewsSourceDAO
❌ NewsLinkDao
```

### DAO 方法
**参照 Java 后端规范**

```python
✅ find_by_resource_id()
✅ find_all_by_status()
✅ find_all()
✅ save()
✅ bulk_insert_ignore()

❌ get_by_resource_id()
❌ get_all()
```

## Repository 命名

### Repository 类
**以 `Repository` 结尾**

```python
✅ NewsLinksCrawlRepository
❌ NewsLinksCrawlRepo
```

### 接口命名
**前缀 `I`**

```python
✅ INewsCrawlRepository
✅ INewsLinkCrawlService
❌ NewsCrawlRepository（接口应加 I）
```

## Mapper 命名

### Mapper 类
**以 `Mapper` 结尾**

```python
✅ NewsSourceMapper
✅ NewsLinkMapper
❌ NewsSourceMap
```

## Service 命名

### 领域服务
**以 `Service` 结尾**

```python
✅ NewsLinkCrawlService
✅ NewsSourceHealthCheckService
❌ NewsLinkCrawl
```

### 应用服务
**以 `ApplicationService` 结尾**

```python
✅ NewsCrawlApplicationService
❌ NewsCrawlService（容易与领域服务混淆）
```

## 文件命名

### Python 文件
**snake_case**

```python
✅ news_link_crawl_service.py
✅ abstract_news_source_config.py
❌ NewsLinkCrawlService.py
❌ abstract-news-source-config.py
```

### 测试文件
**前缀 `test_`**

```python
✅ test_news_link_crawl_service.py
✅ test_registry.py
❌ news_link_crawl_service_test.py
```

### 配置文件
**语义化命名**

```python
✅ straits_times_config.py
✅ jawapos_config.py
❌ config1.py
❌ st_config.py
```

## 目录命名

### 模块目录
**snake_case**

```python
✅ http_news_links_crawl/
✅ single_news_link_crawl/
❌ HttpNewsLinksCrawl/
❌ single-news-link-crawl/
```

### 避免泛化词
**不使用 common、utils、misc**

```python
❌ common/
❌ utils/
❌ misc/
✅ crawler/（明确的功能模块）
✅ config/（明确的功能模块）
```

## 变量命名语义化

### 好的变量名
```python
✅ resource_id
✅ crawl_result
✅ http_adapter
✅ parse_result
```

### 避免的变量名
```python
❌ data
❌ tmp
❌ result（太泛化）
❌ x, y, z（无意义）
```

## 布尔变量命名

### 使用 is/has 前缀
```python
✅ is_active
✅ has_error
✅ is_parse
❌ active
❌ error
```

## 相关链接

- [代码风格](code_style) - 完整代码风格规范
- [实体设计](../02-domain/config/metadata) - 实体示例
- [值对象设计](../02-domain/health_check/status) - 值对象示例
