# NewsSourceMetadata

> 新闻源元数据实体，封装新闻源基本信息

## 设计目的

### 问题
原来新闻源信息散落在多个字段中，不便于管理和传递

### 解决方案
使用不可变值对象封装所有元数据

## 类定义

### 位置
`domain/model/entity/news_source_metadata.py`

### 核心代码
```python
@dataclass(frozen=True)
class NewsSourceMetadata:
    """新闻源元数据（不可变）"""
    
    resource_id: str     # 唯一标识（如 "sg_straits_times"）
    name: str            # 新闻源名称（如 "The Straits Times"）
    domain: str          # 域名（如 "straitstimes.com"）
    url: str             # 主页 URL
    country: str         # 国家代码（如 "SG"）
    language: str        # 语言代码（如 "en"）
    status: NewsSourceStatusVO  # 状态枚举
    
    def __post_init__(self):
        """字段验证"""
        if not self.resource_id:
            raise ValueError("resource_id 不能为空")
        if not self.domain:
            raise ValueError("domain 不能为空")
    
    def is_active(self) -> bool:
        """判断是否可调度"""
        return self.status == NewsSourceStatusVO.NORMAL
```

## 字段说明

### resource_id
**唯一标识**，与数据库 `news_source.resource_id` 对应

**命名规范**：`{country_code}_{source_name}`
- 示例：`sg_straits_times`（新加坡海峡时报）
- 示例：`id_jawapos`（印尼爪哇邮报）

### name
**新闻源名称**，人类可读

- 示例：`"The Straits Times"`
- 示例：`"Jawa Pos"`

### domain
**域名**，不含协议和路径

- 示例：`"straitstimes.com"`
- 示例：`"jawapos.com"`

### url
**主页 URL**，完整链接

- 示例：`"https://www.straitstimes.com"`

### country
**国家代码**，ISO 3166-1 alpha-2

- 示例：`"SG"`（新加坡）
- 示例：`"ID"`（印度尼西亚）

### language
**语言代码**，ISO 639-1

- 示例：`"en"`（英语）
- 示例：`"id"`（印尼语）

### status
**状态枚举**，NewsSourceStatusVO

- `NORMAL = 0` - 正常，可调度
- `DISABLED = 1` - 已禁用，不调度
- `PARSE_ERROR = 2` - 解析异常，待修复

## 数据库映射

### 对应表结构
```sql
CREATE TABLE news_source (
    resource_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    domain VARCHAR(200) NOT NULL,
    url VARCHAR(500) NOT NULL,
    country VARCHAR(10) NOT NULL,
    language VARCHAR(10) NOT NULL,
    status TINYINT DEFAULT 0
);
```

## 不可变性

### 设计原则
使用 `@dataclass(frozen=True)` 保证不可变

**优点**：
- 线程安全
- 避免意外修改
- 可作为字典键
- 语义清晰（值对象）

**使用示例**：
```python
metadata = NewsSourceMetadata(
    resource_id="sg_straits_times",
    name="The Straits Times",
    domain="straitstimes.com",
    url="https://www.straitstimes.com",
    country="SG",
    language="en",
    status=NewsSourceStatusVO.NORMAL
)

# 尝试修改会报错
# metadata.status = NewsSourceStatusVO.DISABLED  # ❌ 错误！
```

## 创建方式

### 1. 从数据库加载
```python
# 通过工厂类加载
metadata = await NewsSourceConfigFactory.load_metadata_from_repository(
    resource_id="sg_straits_times",
    repository=repo
)
```

### 2. 从 JSON 加载
```python
# JSON 文件
{
    "resource_id": "sg_straits_times",
    "name": "The Straits Times",
    "domain": "straitstimes.com",
    "url": "https://www.straitstimes.com",
    "country": "SG",
    "language": "en",
    "status": 0
}

# 加载
metadata = NewsSourceConfigFactory.load_metadata_from_json(
    file_path="configs/straits_times.json"
)
```

### 3. 从字典构造
```python
data = {
    "resource_id": "sg_straits_times",
    "name": "The Straits Times",
    ...
}

metadata = NewsSourceConfigFactory.load_metadata_from_dict(data)
```

## 使用场景

### 在配置类中使用
```python
@NewsSourceConfigRegistry.register("sg_straits_times")
class StraitTimesConfig(AbstractNewsSourceConfig):
    def __init__(self, metadata: NewsSourceMetadata):
        super().__init__(metadata)
        # 可以通过 self.metadata 访问所有字段
```

### 判断是否可调度
```python
if metadata.is_active():
    # 执行爬取
    ...
else:
    # 跳过或记录日志
    logger.warning(f"新闻源 {metadata.name} 状态异常: {metadata.status}")
```

## 状态枚举

### NewsSourceStatusVO
```python
class NewsSourceStatusVO(Enum):
    NORMAL = (0, "正常")
    DISABLED = (1, "已禁用")
    PARSE_ERROR = (2, "解析异常")
```

**详见**：`domain/model/valobj/news_source_status_vo.py`

## 设计优势

### 封装性
- 所有元数据集中管理
- 避免散开的字段

### 类型安全
- 使用 dataclass 和类型注解
- IDE 自动补全和类型检查

### 不可变性
- 线程安全
- 避免意外修改

### 验证机制
- `__post_init__` 验证必填字段
- 保证数据完整性

## 相关链接

- [抽象配置](abstract_config) - 配置类使用元数据
- [工厂模式](factory) - 从多种来源加载元数据
- [数据库设计](../../03-infrastructure/database) - 数据库表结构
