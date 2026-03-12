# 代码风格规范

> 代码注释、命名、类型提示等规范

## 注释规范

### 语言
**统一使用中文**

### 文档字符串（Docstring）
**所有函数必须有 docstring**

```python
def execute_crawl(self, crawl_factor: NewsResourceCrawlFactorEntity):
    \"\"\"
    执行新闻链接爬取
    
    Args:
        crawl_factor: 爬取因子（包含配置和上下文）
    
    Returns:
        CrawlResultEntity: 爬取结果
    \"\"\"
    ...
```

### 行内注释
- 仅用于复杂逻辑
- 不给显而易见的代码写注释
- 保持低密度（约 10-20 行代码 1 条注释）

### 文件头部注释（配置和测试文件）

**配置文件**：
```python
\"\"\"
JawaPos 新闻源配置

配置说明: 印尼 JawaPos 新闻网站的爬虫配置
测试文件: test/xxx/test_xxx.py
测试命令: pytest test/xxx/test_xxx.py::test_xxx

示例:
    config = JawaPosConfig(metadata=...)
\"\"\"
```

**测试文件**：
```python
\"\"\"
NewsLinkCrawlService 集成测试

测试目标: 完整测试 execute_crawl 方法
测试站点: https://www.example.com
运行命令: pytest test/xxx/test_xxx.py

验证内容:
1. 能成功构建 layer 树
2. 能发送 HTTP 请求并解析
3. 分页机制正常工作
\"\"\"
```

## 命名规范

### 基本规则
- **类名**：`PascalCase`（如 `AbstractNewsSourceConfig`）
- **函数/方法**：`snake_case`（如 `build_request`）
- **变量**：`snake_case`
- **常量**：`UPPER_SNAKE_CASE`
- **私有方法**：前缀下划线（如 `_fetch_and_parse`）

### 实体命名
**实体类必须以 `Entity` 结尾**

- ✅ `HealthCheckRecordEntity`
- ✅ `CrawlResultEntity`
- ❌ `HealthCheckRecord`

### DAO 命名
**参照 Java 后端规范**

- **单条查询**：`find_by_xxx()` → `Model | None`
- **列表查询**：`find_all_by_xxx()` → `list[Model]`
- **写操作**：`save()`, `update()`, `delete()`, `bulk_insert_ignore()`

## 值对象设计

### 命名统一
**使用 `Status` 而非 `State`**

- ✅ `NewsSourceStatusVO`
- ❌ `NewsSourceStateVO`

### 设计模式
**二元组 (code, desc)**

```python
class NewsSourceStatusVO(Enum):
    NORMAL = (0, "正常调度")
    DISABLED = (1, "手动停用")
    
    def __init__(self, code: int, desc: str):
        self.code = code
        self.desc = desc
    
    @classmethod
    def from_code(cls, code: int):
        for status in cls:
            if status.code == code:
                return status
        raise ValueError(f"无效的状态码: {code}")
```

## 导包规范

### 统一使用绝对导入
**禁止相对导入**

```python
# ✅ 推荐：绝对导入
from v1.DDD.domain.http_news_links_crawl.model.valobj import NewsSourceStatusVO

# ❌ 禁止：相对导入
from ..model.valobj import NewsSourceStatusVO
```

### 包级别导出
在 `__init__.py` 中统一导出

```python
# __init__.py
from .news_source_status_vo import NewsSourceStatusVO
from .response_parse_result_status_vo import ResponseParseResultStatusVO

__all__ = ["NewsSourceStatusVO", "ResponseParseResultStatusVO"]
```

## 类型提示

- 使用 Python 3.10+ 现代类型提示
- 函数参数和返回值都应有类型注解
- 使用 `dataclass` 定义数据类
- 使用 `ABC` 和 `abstractmethod` 定义抽象类

## 代码组织

**DDD 分层架构**：
- `domain/` - 领域层
- `infrastructure/` - 基础设施层
- `app/` - 应用层
- `api/` - 接口层
- `trigger/` - 触发器层

## Mapper 设计

- **位置**：`infrastructure/persistent/mapper/`
- **命名**：`{ModelName}Mapper`
- **必须方法**：
  - `to_dict(model) -> dict`
  - `to_entity(model) -> Entity`
  - `to_entity_list(models) -> list[Entity]`

## 异步编程

- 使用 `async/await` 进行异步操作
- HTTP 请求使用 httpx 异步客户端
- 数据库操作使用 SQLAlchemy 异步 API

## 错误处理

- 网络请求必须有重试机制、超时控制
- 使用自定义异常类
- 使用 logger 记录错误和调试信息

## 设计原则

- 遵循 SOLID 原则
- 单一职责原则
- 依赖倒置

## 相关链接

- [命名规范](naming) - 详细命名规则
- [测试规范](testing) - 测试相关规范
- [架构原则](../01-architecture/principles) - SOLID 原则
