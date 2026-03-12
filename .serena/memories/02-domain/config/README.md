# 🎯 配置管理概览

> 新闻源配置体系：抽象配置、注册表、工厂模式

## 核心组件

### AbstractNewsSourceConfig
抽象基类，定义新闻源配置接口

### NewsSourceConfigRegistry
注册表，管理配置类的注册和实例化（单例）

### NewsSourceConfigFactory
工厂类，从多种来源加载元数据

### NewsSourceMetadata
元数据实体，封装新闻源基本信息

## 📖 阅读路径

### 实现新闻源配置
```
1. README → 配置体系概览
2. abstract_config → 抽象配置类
3. metadata → 元数据设计
4. registry → 注册表机制（重要）
5. factory → 工厂模式
```

## 📁 本目录文件

- **[abstract_config](abstract_config)** - AbstractNewsSourceConfig 抽象类
- **[metadata](metadata)** - NewsSourceMetadata 元数据实体
- **[registry](registry)** - 注册表机制（装饰器注册+单例）
- **[factory](factory)** - 工厂模式（多数据源加载）

## 使用流程

### 1. 定义配置类
```python
@NewsSourceConfigRegistry.register("sg_straits_times")
class StraitTimesConfig(AbstractNewsSourceConfig):
    def parse_response(self, response):
        # 解析逻辑
        ...
    
    def extract_category(self, params):
        return params.get("category", "unknown")
```

### 2. 导入触发注册
在 `app/src/resource/news_source/__init__.py`：
```python
from .straits_times_config import StraitTimesConfig
```

### 3. 获取配置实例
```python
# 获取单例实例（首次查 DB，后续走缓存）
config = await NewsSourceConfigRegistry.create_config(
    "sg_straits_times",
    repository
)
```

## 设计特点

### 装饰器注册
- 简洁优雅，自动注册
- 防止重复注册
- 类型检查

### 单例模式
- 避免重复查询数据库
- 节省资源

### 元数据驱动
- 元数据与配置分离
- 支持多种数据源（DB/JSON）

## 相关链接

- [爬虫领域](../crawler/README) - 使用配置执行爬取
- [架构模式](../../01-architecture/patterns) - 工厂和注册表模式
