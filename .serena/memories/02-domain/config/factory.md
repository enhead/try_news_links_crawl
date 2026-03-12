# NewsSourceConfigFactory

> 元数据加载工厂，支持多种数据源

## 核心功能

从多种来源加载 NewsSourceMetadata：
1. **数据库** - 通过 Repository 查询
2. **JSON 文件** - 从配置文件加载
3. **字典** - 从字典构造

## 位置
`domain/service/config/news_resource/factory/news_source_config_factory.py`

## 核心方法

### 1. load_metadata_from_repository()

**从数据库加载元数据**

```python
@staticmethod
async def load_metadata_from_repository(
    resource_id: str,
    repository: INewsCrawlRepository
) -> NewsSourceMetadata:
    """
    从数据库查询元数据
    
    Args:
        resource_id: 新闻源唯一标识
        repository: 仓储接口
    
    Returns:
        NewsSourceMetadata: 元数据对象
    
    Raises:
        ValueError: 数据库中不存在该新闻源
    """
    metadata = await repository.get_source_by_resource_id(resource_id)
    
    if metadata is None:
        raise ValueError(
            f"数据库中未找到新闻源: {resource_id}"
        )
    
    return metadata
```

### 2. load_metadata_from_json()

**从 JSON 文件加载**

```python
@staticmethod
def load_metadata_from_json(file_path: str) -> NewsSourceMetadata:
    """
    从 JSON 文件加载元数据
    
    Args:
        file_path: JSON 文件路径
    
    Returns:
        NewsSourceMetadata: 元数据对象
    
    Raises:
        FileNotFoundError: 文件不存在
        JSONDecodeError: JSON 格式错误
        ValueError: 字段缺失或无效
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return NewsSourceConfigFactory.load_metadata_from_dict(data)
```

**JSON 文件格式**：
```json
{
    "resource_id": "sg_straits_times",
    "name": "The Straits Times",
    "domain": "straitstimes.com",
    "url": "https://www.straitstimes.com",
    "country": "SG",
    "language": "en",
    "status": 0
}
```

### 3. load_metadata_from_dict()

**从字典构造**

```python
@staticmethod
def load_metadata_from_dict(data: dict) -> NewsSourceMetadata:
    """
    从字典构造元数据
    
    Args:
        data: 包含元数据字段的字典
    
    Returns:
        NewsSourceMetadata: 元数据对象
    
    Raises:
        ValueError: 字段缺失或无效
    """
    # 验证必填字段
    required_fields = [
        'resource_id', 'name', 'domain',
        'url', 'country', 'language', 'status'
    ]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"缺少必填字段: {field}")
    
    # 构造元数据
    return NewsSourceMetadata(
        resource_id=data['resource_id'],
        name=data['name'],
        domain=data['domain'],
        url=data['url'],
        country=data['country'],
        language=data['language'],
        status=NewsSourceStatusVO(data['status'])
    )
```

## 使用场景

### 场景1：注册表使用（数据库）
```python
# NewsSourceConfigRegistry.create_config() 内部使用
metadata = await NewsSourceConfigFactory.load_metadata_from_repository(
    resource_id="sg_straits_times",
    repository=repo
)

config = StraitTimesConfig(metadata=metadata)
```

### 场景2：配置文件驱动（JSON）
```python
# 从配置文件加载（测试或开发环境）
metadata = NewsSourceConfigFactory.load_metadata_from_json(
    "configs/news_sources/straits_times.json"
)

config = StraitTimesConfig(metadata=metadata)
```

### 场景3：动态构造（字典）
```python
# 从 API 响应或其他来源构造
data = {
    "resource_id": "sg_straits_times",
    "name": "The Straits Times",
    ...
}

metadata = NewsSourceConfigFactory.load_metadata_from_dict(data)
config = StraitTimesConfig(metadata=metadata)
```

## 设计原则

### 工厂只负责加载元数据
- **不涉及**配置类的构造
- **不涉及**配置类的注册
- **职责单一**：元数据加载和验证

### 依赖接口而非实现
- 使用 `INewsCrawlRepository` 接口
- 符合依赖倒置原则（DIP）
- 易于测试（可 mock）

### 完善的错误处理
- 字段验证
- 文件不存在检查
- JSON 格式检查
- 明确的错误信息

## 错误处理

### 数据库不存在
```python
try:
    metadata = await NewsSourceConfigFactory.load_metadata_from_repository(
        "non_existent",
        repo
    )
except ValueError as e:
    logger.error(f"加载元数据失败: {e}")
```

### JSON 文件错误
```python
try:
    metadata = NewsSourceConfigFactory.load_metadata_from_json(
        "invalid.json"
    )
except FileNotFoundError:
    logger.error("配置文件不存在")
except json.JSONDecodeError:
    logger.error("JSON 格式错误")
except ValueError as e:
    logger.error(f"字段验证失败: {e}")
```

### 字段缺失
```python
data = {"resource_id": "test"}  # 缺少其他字段

try:
    metadata = NewsSourceConfigFactory.load_metadata_from_dict(data)
except ValueError as e:
    # "缺少必填字段: name"
    logger.error(e)
```

## 扩展方式

### 未来可扩展
- **从环境变量加载** - `load_metadata_from_env()`
- **从远程 API 加载** - `load_metadata_from_api()`
- **从 YAML 文件加载** - `load_metadata_from_yaml()`

### 扩展示例
```python
@staticmethod
async def load_metadata_from_api(
    resource_id: str,
    api_client: ApiClient
) -> NewsSourceMetadata:
    """从远程 API 加载元数据"""
    response = await api_client.get(f"/news_sources/{resource_id}")
    data = response.json()
    return NewsSourceConfigFactory.load_metadata_from_dict(data)
```

## 与注册表的关系

### 分工明确
- **Factory**：负责元数据加载
- **Registry**：负责配置类注册和实例化

### 配合使用
```python
# Registry 内部使用 Factory（隐式）
config = await NewsSourceConfigRegistry.create_config(
    "sg_straits_times",
    repository
)

# 等价于（显式）
metadata = await NewsSourceConfigFactory.load_metadata_from_repository(
    "sg_straits_times",
    repository
)
config_class = NewsSourceConfigRegistry.get_config_class("sg_straits_times")
config = config_class(metadata=metadata)
```

## 相关链接

- [元数据设计](metadata) - NewsSourceMetadata 详解
- [注册表机制](registry) - 配置类注册
- [仓储接口](../../03-infrastructure/repository) - 数据访问
