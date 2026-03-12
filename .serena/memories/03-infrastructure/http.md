# HTTP 适配器架构

> 多适配器架构，支持 httpx 和 curl_cffi，灵活应对反爬虫挑战

## 架构设计

### 类层次结构

```
BaseHttpAdapter (抽象基类)
    ├── HttpxAdapter   - 标准 HTTP 客户端
    └── CurlCffiAdapter - 模拟浏览器 TLS 指纹（推荐）
```

### 设计原则
- **策略模式**: 统一接口，多种实现
- **依赖倒置**: 上层依赖抽象而非具体实现
- **开闭原则**: 易于扩展新的 HTTP 库

---

## 核心组件

### 1. BaseHttpAdapter (抽象基类)

**位置**: `infrastructure/http/base_http_adapter.py`

**职责**:
- 定义统一的 HTTP 适配器接口
- 提供上下文管理器支持

**核心方法**:
```python
class BaseHttpAdapter(ABC):
    @abstractmethod
    async def send(self, request: RequestParameter) -> Response:
        """发送 HTTP 请求"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """释放连接池资源"""
        pass
```

---

### 2. HttpxAdapter

**位置**: `infrastructure/http/httpx_adapter.py`

**职责**:
- 封装 httpx 异步客户端
- 适用于无反爬虫限制的站点

**特点**:
- ✅ 稳定、成熟的 HTTP 库
- ✅ 完整的 HTTP/1.1 和 HTTP/2 支持
- ❌ 易被 Cloudflare 等 WAF 识别

**配置参数**:
```python
HttpxAdapter(
    timeout=30.0,
    connect_timeout=5.0,
    read_timeout=15.0,
    write_timeout=5.0,
    pool_timeout=5.0,
    max_connections=20,
    max_keepalive_connections=10,
)
```

---

### 3. CurlCffiAdapter (推荐)

**位置**: `infrastructure/http/curl_cffi_adapter.py`

**职责**:
- 使用 curl_cffi 模拟真实浏览器
- 绕过 Cloudflare、DataDome 等反爬虫

**特点**:
- ✅ 模拟浏览器 TLS 指纹 (impersonate)
- ✅ 支持 HTTP/2、HTTP/3
- ✅ 绕过常见反爬虫检测
- ✅ 性能优异

**配置参数**:
```python
CurlCffiAdapter(
    impersonate="chrome120",  # 模拟 Chrome 120
    timeout=30.0,
    connect_timeout=5.0,
    read_timeout=15.0,
    max_connections=20,
)
```

**可用的 impersonate 值**:
- `chrome120`, `chrome110`, `chrome99`
- `safari15_5`, `safari15_3`
- `edge101`, `edge99`

---

## 配置系统

### 配置层级

```
全局默认配置 (.env)
    ↓
新闻源级别覆盖 (可选)
    ↓
实际使用的适配器
```

### 1. 全局配置

**文件**: `.env`

```bash
# 适配器选择
HTTP_DEFAULT_ADAPTER=curl_cffi  # 或 httpx

# curl_cffi 特有配置
HTTP_CURL_CFFI_IMPERSONATE=chrome120

# 通用配置
HTTP_TIMEOUT=30
HTTP_CONNECT_TIMEOUT=5
HTTP_READ_TIMEOUT=15
HTTP_MAX_CONNECTIONS=20
```

### 2. 新闻源级别覆盖

**使用场景**: 某些新闻源需要特殊配置

**示例**:
```python
# berita_harian_config.py
super().__init__(
    metadata=metadata,
    layer_schema=layer_schema,
    template_request_config=request_template,
    http_adapter_overrides={
        "adapter_type": "curl_cffi",     # 强制使用 curl_cffi
        "impersonate": "safari15_5",     # 覆盖模拟浏览器
        "timeout": 60.0,                 # 覆盖超时时间
    }
)
```

---

## 异常处理

### 统一异常

两个适配器都抛出统一的业务异常：

```python
# 网络层错误（可重试）
class HttpRequestError(Exception):
    """超时、连接失败等"""
    
# HTTP 状态码错误
class HttpStatusError(Exception):
    """4xx、5xx 状态码"""
```

### 异常翻译

内部实现自动翻译底层异常：
- httpx 异常 → 统一异常
- curl_cffi 异常 → 统一异常

**优势**: 上层代码无需感知具体 HTTP 库

---

## DI 容器集成

**位置**: `app/src/main/DI/container.py`

**工厂函数**:
```python
def _create_http_adapter(http_config):
    """根据配置动态创建适配器"""
    adapter_type = http_config.default_adapter
    
    if adapter_type == "curl_cffi":
        return CurlCffiAdapter(...)
    elif adapter_type == "httpx":
        return HttpxAdapter(...)
    else:
        raise ValueError(f"未知适配器: {adapter_type}")
```

**注册**:
```python
http_adapter = providers.Singleton(
    _create_http_adapter,
    http_config=config.provided.http,
)
```

---

## 使用建议

### 选择适配器

| 场景 | 推荐适配器 | 原因 |
|------|-----------|------|
| 无反爬虫站点 | HttpxAdapter | 稳定、成熟 |
| Cloudflare 保护 | CurlCffiAdapter | 绕过检测 |
| 高频爬取 | CurlCffiAdapter | 更真实的浏览器特征 |
| 一般爬虫 | CurlCffiAdapter | 推荐默认 |

### 性能优化

- ✅ 使用单例模式，复用连接池
- ✅ 合理配置 `max_connections`
- ✅ 使用 `async with` 自动释放资源
- ✅ 针对慢速站点增大超时时间

### 故障排查

**症状**: 403 Forbidden
- 尝试切换到 CurlCffiAdapter
- 更换 impersonate 浏览器类型
- 检查 User-Agent 是否合理

**症状**: 超时频繁
- 增大 timeout 配置
- 检查网络连接
- 考虑使用代理

---

## 扩展性

### 添加新适配器

1. 继承 `BaseHttpAdapter`
2. 实现 `send()` 和 `close()` 方法
3. 翻译异常为 `HttpRequestError` 和 `HttpStatusError`
4. 在 `_create_http_adapter()` 工厂函数中注册

**示例**:
```python
class AiohttpAdapter(BaseHttpAdapter):
    async def send(self, request: RequestParameter) -> Response:
        # 实现逻辑
        ...
    
    async def close(self) -> None:
        # 释放资源
        ...
```

---

## 相关链接

- [应用配置](../04-application/config) - HttpConfig
- [DI 容器](../04-application/di_container) - 适配器工厂
- [爬取节点](../02-domain/crawler/nodes) - 使用适配器
- [新闻源配置](../02-domain/config/abstract_config) - 适配器覆盖
