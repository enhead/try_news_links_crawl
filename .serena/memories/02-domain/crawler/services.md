# 爬虫领域服务

> INewsLinkCrawlService 接口和实现

## 领域服务定义

### INewsLinkCrawlService

**职责**：
- 构建 Layer 树
- 执行爬取流程
- 返回爬取结果

**位置**：`domain/service/single_news_link_crawl/base_news_link_crawl_service.py`

**接口定义**：
```python
class INewsLinkCrawlService(ABC):
    @abstractmethod
    async def execute_crawl(
        self,
        crawl_factor: NewsResourceCrawlFactorEntity
    ) -> CrawlResultEntity:
        """
        执行新闻链接爬取
        
        Args:
            crawl_factor: 爬取因子（包含配置和上下文）
        
        Returns:
            CrawlResultEntity: 爬取结果
        """
        pass
```

## 实现类

### NewsLinkCrawlService

**位置**：`domain/service/single_news_link_crawl/impl/news_link_crawl_service.py`

**核心方法**：

#### 1. execute_crawl()
```python
async def execute_crawl(
    self,
    crawl_factor: NewsResourceCrawlFactorEntity
) -> CrawlResultEntity:
    """
    执行爬取的主流程
    
    流程：
    1. 获取 layer_schema
    2. 构建 Layer 树
    3. 创建初始 factor
    4. 执行 Layer 树
    5. 返回结果
    """
    # 获取层配置
    layer_schema = crawl_factor.source_config.layer_schema
    
    # 构建 Layer 树
    root_layer = self._build_layer_tree(
        layer_schema,
        crawl_factor.context
    )
    
    # 创建初始 factor
    factor = LayerFactorEntity(
        params={},
        context=crawl_factor.context
    )
    
    # 执行爬取
    result = await root_layer.execute(factor)
    
    return result
```

#### 2. _build_layer_tree()
```python
def _build_layer_tree(
    self,
    schemas: List[dict],
    context: CrawlContext
) -> AbstractCrawlLayer:
    """
    从内到外构建 Layer 树
    
    Args:
        schemas: 层配置列表
        context: 爬取上下文
    
    Returns:
        AbstractCrawlLayer: 根层
    """
    next_layer = None
    
    # 从最内层（叶子层）开始构建
    for schema in reversed(schemas):
        layer = CrawlLayerFactory.build(
            schema=schema,
            next_layer=next_layer,
            context=context
        )
        next_layer = layer
    
    return next_layer
```

## 输入参数

### NewsResourceCrawlFactorEntity

**字段**：
- `source_config: AbstractNewsSourceConfig` - 新闻源配置
- `context: CrawlContext` - 爬取上下文

**创建示例**：
```python
crawl_factor = NewsResourceCrawlFactorEntity(
    source_config=config,
    context=CrawlContext(
        source_config=config,
        http_adapter=adapter,
        repository=repo
    )
)
```

## 返回结果

### CrawlResultEntity

**字段**：
- `total_new: int` - 总新增链接数
- `total_duplicate: int` - 总重复链接数
- `sub_results: List[CrawlResultEntity]` - 子结果列表（层级结构）
- `errors: List[str]` - 错误信息列表

**示例**：
```python
result = CrawlResultEntity(
    total_new=150,
    total_duplicate=50,
    sub_results=[
        # politics 栏目结果
        CrawlResultEntity(total_new=100, ...),
        # tech 栏目结果
        CrawlResultEntity(total_new=50, ...)
    ],
    errors=[]
)
```

## 调用方式

### 从应用服务调用

```python
# Application 层
class NewsCrawlApplicationService:
    def __init__(
        self,
        crawl_service: INewsLinkCrawlService,
        registry: NewsSourceConfigRegistry,
        repository: INewsCrawlRepository
    ):
        self.crawl_service = crawl_service
        self.registry = registry
        self.repository = repository
    
    async def crawl_single_source(self, resource_id: str):
        # 1. 获取配置
        config = await self.registry.create_config(
            resource_id,
            self.repository
        )
        
        # 2. 创建 crawl_factor
        crawl_factor = NewsResourceCrawlFactorEntity(
            source_config=config,
            context=CrawlContext(
                source_config=config,
                http_adapter=self.http_adapter,
                repository=self.repository
            )
        )
        
        # 3. 调用领域服务
        result = await self.crawl_service.execute_crawl(crawl_factor)
        
        return result
```

## 领域服务 vs 应用服务

### 领域服务（NewsLinkCrawlService）
- **职责**：纯业务逻辑（Layer 树构建和执行）
- **不包含**：配置加载、错误处理、日志记录
- **返回**：CrawlResultEntity（领域对象）

### 应用服务（NewsCrawlApplicationService）
- **职责**：编排领域服务、错误处理、日志记录
- **包含**：配置加载、事务管理、对外接口
- **返回**：API 响应对象（DTO）

## 测试

### 单元测试示例

```python
@pytest.mark.asyncio
async def test_execute_crawl():
    # Mock 依赖
    mock_config = MockNewsSourceConfig(...)
    mock_adapter = MockHttpAdapter()
    mock_repo = MockRepository()
    
    # 创建服务
    service = NewsLinkCrawlService()
    
    # 创建 crawl_factor
    crawl_factor = NewsResourceCrawlFactorEntity(
        source_config=mock_config,
        context=CrawlContext(
            source_config=mock_config,
            http_adapter=mock_adapter,
            repository=mock_repo
        )
    )
    
    # 执行
    result = await service.execute_crawl(crawl_factor)
    
    # 断言
    assert result.total_new > 0
    assert len(result.errors) == 0
```

## 相关链接

- [执行流程](execution_flow) - 完整的执行流程图解
- [应用服务](../../04-application/services) - 应用层服务
- [配置管理](../config/README) - 新闻源配置体系
