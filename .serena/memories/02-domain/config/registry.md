# NewsSourceConfigRegistry

> 配置注册表：装饰器注册 + 单例工厂

## 核心功能

### 两层能力
1. **纯注册表**：装饰器注册 + 类查找（无副作用）
2. **单例工厂**：`create_config()` 负责查 DB、实例化、缓存

## 位置
`domain/service/config/news_resource/registry/news_source_config_registry.py`

## 核心方法

### 1. register() - 装饰器注册

**用法**：
```python
@NewsSourceConfigRegistry.register("sg_straits_times")
class StraitTimesConfig(AbstractNewsSourceConfig):
    ...
```

**实现**：
```python
@classmethod
def register(cls, resource_id: str):
    def decorator(config_class: Type[AbstractNewsSourceConfig]):
        # 防重复注册
        if resource_id in cls._registry:
            raise ValueError(
                f"配置类已注册: resource_id={resource_id}"
            )
        
        # 类型检查
        if not issubclass(config_class, AbstractNewsSourceConfig):
            raise TypeError(
                f"配置类必须继承 AbstractNewsSourceConfig"
            )
        
        # 注册
        cls._registry[resource_id] = config_class
        return config_class
    
    return decorator
```

**特点**：
- ✅ 防止重复注册（抛出 ValueError）
- ✅ 类型检查（必须继承 AbstractNewsSourceConfig）
- ✅ 自动注册（模块导入时执行）

### 2. get_config_class() - 获取类

**用法**：
```python
# 获取类（不实例化）
cls = NewsSourceConfigRegistry.get_config_class("sg_straits_times")
```

**实现**：
```python
@classmethod
def get_config_class(
    cls,
    resource_id: str
) -> Type[AbstractNewsSourceConfig]:
    if resource_id not in cls._registry:
        raise KeyError(
            f"未找到配置类: resource_id={resource_id}"
        )
    return cls._registry[resource_id]
```

### 3. create_config() - 获取实例（单例）

**用法**：
```python
# 首次调用：查 DB + 实例化 + 缓存
config1 = await NewsSourceConfigRegistry.create_config(
    "sg_straits_times",
    repository
)

# 后续调用：直接返回缓存
config2 = await NewsSourceConfigRegistry.create_config(
    "sg_straits_times",
    repository
)

assert config1 is config2  # True - 同一个对象
```

**实现**：
```python
@classmethod
async def create_config(
    cls,
    resource_id: str,
    repository: INewsCrawlRepository
) -> AbstractNewsSourceConfig:
    # 如果已缓存，直接返回
    if resource_id in cls._instances:
        return cls._instances[resource_id]
    
    # 获取配置类
    config_class = cls.get_config_class(resource_id)
    
    # 从数据库查询元数据
    metadata = await repository.get_source_by_resource_id(resource_id)
    if metadata is None:
        raise ValueError(f"数据库中未找到新闻源: {resource_id}")
    
    # 实例化
    instance = config_class(metadata=metadata)
    
    # 缓存
    cls._instances[resource_id] = instance
    
    return instance
```

**特点**：
- ✅ 单例缓存（避免重复查询数据库）
- ✅ 按需加载（首次使用才查询）
- ✅ 自动验证（数据库不存在时抛异常）

### 4. 辅助方法

#### has_config() - 检查是否注册
```python
if NewsSourceConfigRegistry.has_config("sg_straits_times"):
    # 已注册
    ...
```

#### list_registered() - 列出所有注册
```python
registered = NewsSourceConfigRegistry.list_registered()
# ["sg_straits_times", "id_jawapos", ...]
```

#### clear_cache() - 清除缓存
```python
# 清除单个缓存
NewsSourceConfigRegistry.clear_cache("sg_straits_times")

# 清除全部缓存
NewsSourceConfigRegistry.clear_cache()
```

#### clear_registry() - 清空注册表（仅测试）
```python
NewsSourceConfigRegistry.clear_registry()
```

## 使用流程

### 1. 定义配置类
```python
# src/v1/DDD/app/src/resource/news_source/straits_times_config.py

@NewsSourceConfigRegistry.register("sg_straits_times")
class StraitTimesConfig(AbstractNewsSourceConfig):
    def parse_response(self, response):
        ...
    
    def extract_category(self, params):
        return params.get("category", "unknown")
```

### 2. 统一导入（触发注册）
```python
# src/v1/DDD/app/src/resource/news_source/__init__.py

from .straits_times_config import StraitTimesConfig
from .jawapos_config import JawaPosConfig
# ... 导入所有配置类

__all__ = [
    "StraitTimesConfig",
    "JawaPosConfig",
]
```

**重要**：
- 配置类必须被导入，装饰器才会执行
- 建议在 `__init__.py` 中统一导入
- 应用启动时导入此模块

### 3. 使用配置
```python
# 在应用服务中使用
config = await NewsSourceConfigRegistry.create_config(
    "sg_straits_times",
    repository
)

# 使用配置执行爬取
result = await crawl_service.execute_crawl(
    NewsResourceCrawlFactorEntity(source_config=config, ...)
)
```

## 内部存储

### 类变量
```python
class NewsSourceConfigRegistry:
    _registry: Dict[str, Type[AbstractNewsSourceConfig]] = {}
    _instances: Dict[str, AbstractNewsSourceConfig] = {}
```

- `_registry` - 存储 resource_id → 配置类的映射
- `_instances` - 存储 resource_id → 配置实例的映射（单例缓存）

## 单例模式

### 为什么使用单例？
- **避免重复查询数据库**：元数据查询成本高
- **节省资源**：配置对象可复用
- **状态共享**：全局唯一配置实例

### 单例验证
```python
config1 = await NewsSourceConfigRegistry.create_config("sg_straits_times", repo)
config2 = await NewsSourceConfigRegistry.create_config("sg_straits_times", repo)

assert config1 is config2  # True
assert id(config1) == id(config2)  # 同一个对象
```

## 测试支持

### 清理注册表
```python
@pytest.fixture(autouse=True)
def clean_registry():
    """每个测试前后清空注册表"""
    NewsSourceConfigRegistry.clear_registry()
    yield
    NewsSourceConfigRegistry.clear_registry()
```

### 清理缓存
```python
# 测试前清理缓存
NewsSourceConfigRegistry.clear_cache()

# 测试单例失效
config1 = await NewsSourceConfigRegistry.create_config("test", repo)
NewsSourceConfigRegistry.clear_cache("test")
config2 = await NewsSourceConfigRegistry.create_config("test", repo)

assert config1 is not config2  # 缓存已清除，重新创建
```

## 防御性检查

### 重复注册检查
```python
@NewsSourceConfigRegistry.register("duplicate")
class FirstConfig(AbstractNewsSourceConfig):
    ...

@NewsSourceConfigRegistry.register("duplicate")
class SecondConfig(AbstractNewsSourceConfig):  # ❌ ValueError
    ...
```

### 类型检查
```python
@NewsSourceConfigRegistry.register("invalid")
class InvalidClass:  # ❌ TypeError
    # 未继承 AbstractNewsSourceConfig
    ...
```

### 数据库存在性检查
```python
# 注册了配置类，但数据库中没有对应记录
config = await NewsSourceConfigRegistry.create_config(
    "non_existent",
    repo
)  # ❌ ValueError: 数据库中未找到新闻源
```

## 设计优势

### 装饰器注册
- 简洁优雅
- 自动注册（模块导入时）
- 防止遗漏

### 单例缓存
- 避免重复查询
- 节省资源
- 性能优化

### 按需加载
- 首次使用才查询数据库
- 延迟初始化
- 减少启动时间

### 类型安全
- 编译时检查继承关系
- IDE 自动补全
- 运行时验证

## 注意事项

### ⚠️ 模块导入时机
配置类必须在应用启动时被导入，否则装饰器不会执行

**建议做法**：
```python
# app/src/resource/news_source/__init__.py
from .straits_times_config import StraitTimesConfig
from .jawapos_config import JawaPosConfig

# main.py 或 application.py
import app.src.resource.news_source  # 触发导入
```

### ⚠️ 全局状态共享
注册表是类级别变量，在整个应用生命周期中全局共享

### ⚠️ 单例修改影响全局
修改配置实例会影响所有使用该配置的地方

## 相关链接

- [抽象配置](abstract_config) - 配置类基类
- [元数据设计](metadata) - NewsSourceMetadata
- [工厂模式](factory) - 元数据加载
- [架构模式](../../01-architecture/patterns) - 注册表模式详解
