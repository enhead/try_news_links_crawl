# 爬取节点

> 负责单次 HTTP 请求、解析、去重和保存

## DefaultCrawlNode

### 职责
执行单次爬取任务，包含完整的请求-解析-去重-保存流程

### 位置
`domain/service/single_news_link_crawl/crawl_layer/crawl_node/impl/default_crawl_node.py`

## 执行流程

### 完整流程
```
1. 构建请求   → source_config.build_request()
2. 发送请求   → http_adapter.send()
3. 解析响应   → source_config.parse_response()
4. 批量去重   → repository.check_exists_batch()
5. 批量保存   → repository.save_batch()
6. 返回结果   → CrawlNodeResultEntity
```

### 代码示例
```python
class DefaultCrawlNode:
    def __init__(self, context: CrawlContext):
        self.source_config = context.source_config
        self.http_adapter = context.http_adapter
        self.repository = context.repository
    
    async def execute(self, params: dict) -> CrawlNodeResultEntity:
        # 1. 构建请求
        request = self.source_config.build_request(params)
        
        # 2. 发送请求
        response = await self.http_adapter.send(request)
        
        # 3. 解析响应
        parse_result = self.source_config.parse_response(response)
        
        # 4. 批量去重
        new_links = await self.repository.check_exists_batch(
            aggregate
        )
        
        # 5. 批量保存（新增）
        await self.repository.save_batch(new_links)
        
        # 6. 返回结果
        return CrawlNodeResultEntity(
            new_count=len(new_links),
            duplicate_count=duplicate_count,
            ...
        )
```

## 职责下沉设计

### 为什么保存操作在 Node 层？
- **即时保存**：减少内存占用
- **职责清晰**：Node 负责完整的爬取流程
- **错误隔离**：单次失败不影响其他爬取

### 之前的设计（已废弃）
```
Layer 层收集所有结果 → 最后统一保存
❌ 问题：内存占用大，失败影响全局
```

### 当前设计
```
Node 每次爬取后立即保存
✅ 优点：内存占用小，故障隔离
```

## 抽象基类

### AbstractCrawlNode
**位置**：`domain/service/single_news_link_crawl/crawl_layer/crawl_node/abstract_crawl_node.py`

**核心方法**：
- `execute(params)` - 抽象方法，子类实现具体逻辑

## 爬取上下文

### CrawlContext
**包含的依赖**：
- `source_config: AbstractNewsSourceConfig` - 新闻源配置
- `http_adapter: HttpAdapter` - HTTP 客户端
- `repository: INewsCrawlRepository` - 数据仓储

**传递方式**：
```python
context = CrawlContext(
    source_config=config,
    http_adapter=adapter,
    repository=repo
)
node = DefaultCrawlNode(context)
```

## 错误处理

### HTTP 错误
- `HttpRequestError` - 网络错误
- `HttpStatusError` - HTTP 状态码错误
- 使用 tenacity 实现重试机制

### 解析错误
- 记录错误日志
- 返回空结果（不中断流程）

### 数据库错误
- 记录错误日志
- 抛出异常（中断流程）

## 返回结果

### CrawlNodeResultEntity
**字段**：
- `new_count` - 新增链接数
- `duplicate_count` - 重复链接数
- `error_message` - 错误信息（可选）
- `urls` - 链接列表

## 扩展节点类型

### 未来可扩展
- **CacheCrawlNode** - 带缓存的爬取节点
- **RateLimitCrawlNode** - 带限流的爬取节点
- **ProxyCrawlNode** - 使用代理的爬取节点

### 策略模式
不同节点实现不同的爬取策略，统一的 `execute()` 接口

## 异步执行

### 当前实现
- 使用 `async/await` 异步执行
- 单节点异步（HTTP + 数据库）

### 未来优化
- 并发爬取多个节点
- 连接池优化
- 批量操作性能调优

## 相关链接

- [爬虫层类型](layers) - Layer 调用 Node
- [执行流程](execution_flow) - 完整流程图解
- [配置管理](../config/abstract_config) - source_config 接口
