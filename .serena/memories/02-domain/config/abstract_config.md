# AbstractNewsSourceConfig

> 新闻源配置抽象基类，定义配置接口

## 职责

### 核心方法
1. **build_request()** - 构建 HTTP 请求
2. **build_health_check_params_list()** - 构建健康检查参数列表
3. **parse_response()** - 解析 HTTP 响应
4. **extract_category()** - 提取栏目分类

## 类定义

### 位置
`domain/service/config/news_resource/abstract_news_source_config.py`

### 核心代码
```python
class AbstractNewsSourceConfig(ABC):
    def __init__(
        self,
        metadata: NewsSourceMetadata,
        layer_schema: Optional[List[dict]] = None,
        template_request_config: Optional[dict] = None
    ):
        self.metadata = metadata
        self.layer_schema = layer_schema or []
        self.template_request_config = template_request_config or {}
    
    @property
    def source_id(self) -> str:
        """新闻源唯一标识"""
        return self.metadata.resource_id
    
    @property
    def name(self) -> str:
        """新闻源名称"""
        return self.metadata.name
    
    @abstractmethod
    def parse_response(
        self,
        response: Response
    ) -> ResponseParseResultEntity:
        """
        解析响应，提取新闻链接
        
        Args:
            response: HTTP 响应对象
        
        Returns:
            ResponseParseResultEntity: 解析结果（包含 URLs 和状态）
        """
        pass
    
    @abstractmethod
    def extract_category(self, params: dict) -> str:
        """
        从爬取参数中提取栏目分类
        
        Args:
            params: 爬取参数字典
        
        Returns:
            str: 栏目分类（如 "politics", "tech"）
        """
        pass
    
    def build_request(self, params: dict) -> RequestParameter:
        """
        构建 HTTP 请求（有默认实现）
        
        基于 template_request_config 填充参数
        """
        # 默认实现：URL 模板填充
        ...
```

## 使用示例

### 实现子类

```python
@NewsSourceConfigRegistry.register("sg_straits_times")
class StraitTimesConfig(AbstractNewsSourceConfig):
    """海峡时报配置"""
    
    def parse_response(
        self,
        response: Response
    ) -> ResponseParseResultEntity:
        try:
            # 解析 HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取链接
            urls = []
            for link in soup.find_all('a', class_='article-link'):
                url = link.get('href')
                if url:
                    urls.append(urljoin(self.metadata.domain, url))
            
            return ResponseParseResultEntity(
                status=ResponseParseResultStatusVO.SUCCESS,
                urls=urls,
                errors=[]
            )
        except Exception as e:
            return ResponseParseResultEntity(
                status=ResponseParseResultStatusVO.PARSE_ERROR,
                urls=[],
                errors=[str(e)]
            )
    
    def extract_category(self, params: dict) -> str:
        """从参数中提取分类"""
        return params.get("category", "general")
```

## 配置字段

### metadata（必需）
**类型**：`NewsSourceMetadata`

**包含信息**：
- `resource_id` - 唯一标识
- `name` - 新闻源名称
- `domain` - 域名
- `url` - 主页 URL
- `country` - 国家代码
- `language` - 语言代码
- `status` - 状态（0=正常,1=禁用,2=异常）

### layer_schema（可选）
**类型**：`List[dict]`

**用途**：定义爬取层结构

**示例**：
```python
layer_schema = [
    {
        "type": "enumerable",
        "param_name": "category",
        "values": ["politics", "tech", "sports"]
    },
    {
        "type": "sequential",
        "param_name": "page",
        "start": 1,
        "step": 1
    }
]
```

### template_request_config（可选）
**类型**：`dict`

**用途**：HTTP 请求模板配置

**示例**：
```python
template_request_config = {
    "method": "GET",
    "url_template": "https://example.com/news?category={category}&page={page}",
    "headers": {
        "User-Agent": "Mozilla/5.0..."
    },
    "timeout": 30
}
```

## 便捷属性

### 向后兼容
通过 `@property` 提供便捷访问：

```python
config.source_id   # → metadata.resource_id
config.name        # → metadata.name
config.domain      # → metadata.domain
config.country     # → metadata.country
config.language    # → metadata.language
```

## 健康检查参数生成

### build_health_check_params_list()
**有默认实现（支持参数化配置）**

**职责**：
- 为健康检查生成测试参数列表
- 支持通过 `health_check` 字段自定义策略
- 默认策略：第一层枚举遍历，其他层取首值

**配置选项**：
```python
layer_schema = [
    {
        "type": "enumerable",
        "param_name": "category",
        "values": ["politics", "tech", "sports"],
        "health_check": "all"  # 遍历所有值（默认第一层自动遍历）
    },
    {
        "type": "enumerable",
        "param_name": "subcategory",
        "values": ["local", "world"],
        "health_check": "first"  # 只取第一个值
    },
    {
        "type": "sequential",
        "param_name": "page",
        "start": 1,
        "end": 10
        # 不指定 health_check，默认只取起始值
    }
]
```

**返回示例**：
```python
# 默认策略（遍历第一层枚举）
config.build_health_check_params_list()
# -> [
#      {"category": "politics", "page": 1},
#      {"category": "tech", "page": 1},
#      {"category": "sports", "page": 1}
#    ]

# 显式配置多层遍历（笛卡尔积）
# 如果两层都配置 "health_check": "all"
# -> [
#      {"cat1": "a", "cat2": "x", "page": 1},
#      {"cat1": "a", "cat2": "y", "page": 1},
#      {"cat1": "b", "cat2": "x", "page": 1},
#      {"cat1": "b", "cat2": "y", "page": 1}
#    ]
```

**子类可重写**：
```python
class CustomConfig(AbstractNewsSourceConfig):
    def build_health_check_params_list(self):
        # 自定义健康检查策略
        return [{"special_param": "value"}]
```

## 抽象方法说明

### parse_response()
**必须实现**

**职责**：
- 从 HTTP 响应中提取新闻链接
- 处理 HTML/JSON 等不同格式
- 错误处理和日志记录

**返回**：
```python
ResponseParseResultEntity(
    status=ResponseParseResultStatusVO.SUCCESS,
    urls=["https://...", ...],
    errors=[]
)
```

### extract_category()
**必须实现**

**职责**：
- 从爬取参数中提取栏目分类
- 用于保存到 `news_link.category` 字段

**示例**：
```python
def extract_category(self, params: dict) -> str:
    # 方式1：直接从参数提取
    return params.get("category", "general")
    
    # 方式2：映射转换
    category_map = {
        "pol": "politics",
        "tec": "technology"
    }
    return category_map.get(params.get("cat"), "unknown")
```

## 设计优势

### 模板方法模式
- 定义统一流程
- 子类只需实现特定步骤
- 易于扩展新闻源

### 元数据封装
- 使用 NewsSourceMetadata 统一管理
- 避免散开的字段
- 支持多种数据源

### 默认实现
- `build_request()` 有默认实现
- 减少子类重复代码
- 特殊需求可重写

## 相关链接

- [元数据设计](metadata) - NewsSourceMetadata 详解
- [注册表机制](registry) - 配置类注册
- [爬取节点](../crawler/nodes) - Node 调用配置方法
