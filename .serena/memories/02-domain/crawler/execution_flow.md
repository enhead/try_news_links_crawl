# 爬虫执行流程

> Layer 树构建和递归执行的完整流程

## 总体流程

### 高层流程
```
1. 应用服务调用领域服务
2. 领域服务构建 Layer 树
3. 递归执行 Layer 树
4. 返回爬取结果
```

## 详细流程

### 1. 领域服务入口

**NewsLinkCrawlService.execute_crawl()**

```python
async def execute_crawl(
    self, 
    crawl_factor: NewsResourceCrawlFactorEntity
) -> CrawlResultEntity:
    # 1. 从 source_config 获取 layer_schema
    layer_schema = crawl_factor.source_config.layer_schema
    
    # 2. 构建 Layer 树
    root_layer = self._build_layer_tree(layer_schema)
    
    # 3. 创建初始 LayerFactorEntity
    factor = LayerFactorEntity(
        params={},
        context=crawl_factor.context
    )
    
    # 4. 执行 Layer 树
    result = await root_layer.execute(factor)
    
    return result
```

### 2. Layer 树构建

**CrawlLayerFactory.build()**

```python
def _build_layer_tree(self, schemas: List[dict]):
    """
    从内到外构建 Layer 树
    
    示例：
    schemas = [
        {"type": "enumerable", "param_name": "category", ...},
        {"type": "mapping", "param_name": "subcategory", ...},
        {"type": "sequential", "param_name": "page", ...}
    ]
    
    构建结果：
    EnumerableLayer
      └─ MappingLayer
          └─ SequentialLayer
    """
    next_layer = None
    
    # 从最内层（叶子层）开始构建
    for schema in reversed(schemas):
        layer = CrawlLayerFactory.build(
            schema=schema,
            next_layer=next_layer,
            context=self.context
        )
        next_layer = layer
    
    return next_layer  # 返回根层
```

### 3. Layer 递归执行

**EnumerableLayer.execute()**

```python
async def execute(self, factor: LayerFactorEntity):
    results = []
    
    # 遍历枚举值
    for value in self.values:
        # 合并参数
        new_params = {
            **factor.params,
            self.param_name: value
        }
        
        # 创建新 factor
        new_factor = LayerFactorEntity(
            params=new_params,
            context=factor.context
        )
        
        # 如果有下一层，递归调用
        if self.next_layer:
            result = await self.next_layer.execute(new_factor)
            results.append(result)
    
    # 合并所有结果
    return self._merge_results(results)
```

**MappingLayer.execute()**

```python
async def execute(self, factor: LayerFactorEntity):
    results = []
    
    # 获取依赖参数的值
    depend_value = factor.params[self.depends_on]
    
    # 根据映射关系获取值列表
    values = self.mapping[depend_value]
    
    # 遍历映射值
    for value in values:
        new_params = {
            **factor.params,
            self.param_name: value
        }
        
        new_factor = LayerFactorEntity(
            params=new_params,
            context=factor.context
        )
        
        if self.next_layer:
            result = await self.next_layer.execute(new_factor)
            results.append(result)
    
    return self._merge_results(results)
```

**SequentialLayer.execute()**

```python
async def execute(self, factor: LayerFactorEntity):
    prune_state = PruneState()
    current = self.start
    results = []
    
    # 循环翻页
    while True:
        # 合并参数
        params = {
            **factor.params,
            self.param_name: current
        }
        
        # 创建节点并执行
        node = DefaultCrawlNode(factor.context)
        node_result = await node.execute(params)
        results.append(node_result)
        
        # 更新剪枝状态
        prune_state.update(node_result)
        
        # 检查是否停止
        if prune_state.should_stop():
            break
        
        current += self.step
    
    return self._merge_results(results)
```

### 4. Node 执行爬取

**DefaultCrawlNode.execute()**

```python
async def execute(self, params: dict):
    # 1. 构建请求
    request = self.source_config.build_request(params)
    
    # 2. 发送请求
    response = await self.http_adapter.send(request)
    
    # 3. 解析响应
    parse_result = self.source_config.parse_response(response)
    
    # 4. 提取分类
    category = self.source_config.extract_category(params)
    
    # 5. 构建聚合
    aggregate = NewsLinkBatchAggregate(
        urls=parse_result.urls,
        resource_id=self.source_config.source_id,
        category=category
    )
    
    # 6. 批量去重
    new_aggregate = await self.repository.check_exists_batch(
        aggregate
    )
    
    # 7. 批量保存
    await self.repository.save_batch(new_aggregate)
    
    # 8. 返回结果
    return CrawlNodeResultEntity(
        new_count=len(new_aggregate.links),
        duplicate_count=len(aggregate.links) - len(new_aggregate.links),
        urls=parse_result.urls
    )
```

## 完整流程图

```
NewsCrawlApplicationService (Application 层)
  └─ NewsLinkCrawlService.execute_crawl() (Domain 层)
      │
      ├─ 1. 构建 Layer 树
      │   └─ CrawlLayerFactory.build()
      │       └─ EnumerableLayer
      │           └─ MappingLayer
      │               └─ SequentialLayer
      │
      └─ 2. 执行 Layer 树
          └─ EnumerableLayer.execute()
              ├─ value="politics"
              │   └─ MappingLayer.execute()
              │       ├─ value="domestic"
              │       │   └─ SequentialLayer.execute()
              │       │       ├─ page=1
              │       │       │   └─ DefaultCrawlNode.execute()
              │       │       │       ├─ build_request()
              │       │       │       ├─ send()
              │       │       │       ├─ parse_response()
              │       │       │       ├─ check_exists_batch()
              │       │       │       └─ save_batch()
              │       │       │
              │       │       ├─ page=2
              │       │       │   └─ DefaultCrawlNode.execute()
              │       │       │
              │       │       └─ page=3 (剪枝停止)
              │       │
              │       └─ value="international"
              │           └─ SequentialLayer.execute()
              │
              ├─ value="tech"
              │   └─ ...
              │
              └─ value="sports"
                  └─ ...
```

## 参数传递示例

### 三层嵌套的参数合并

```python
# 初始参数
params = {}

# EnumerableLayer 添加
params = {"category": "politics"}

# MappingLayer 添加
params = {"category": "politics", "subcategory": "domestic"}

# SequentialLayer 添加
params = {"category": "politics", "subcategory": "domestic", "page": 1}

# 最终用于构建请求
# URL: /news?category=politics&subcategory=domestic&page=1
```

## 结果合并

### 层级结果合并
每层将子层的结果合并返回：

```python
def _merge_results(self, results: List[CrawlResultEntity]):
    return CrawlResultEntity(
        total_new=sum(r.total_new for r in results),
        total_duplicate=sum(r.total_duplicate for r in results),
        sub_results=results
    )
```

## 异步执行

### 当前实现
- Layer 内顺序执行（for 循环）
- Node 内异步执行（HTTP + DB）

### 未来优化
- Layer 内并发执行（asyncio.gather）
- 控制并发数（semaphore）

## 相关链接

- [爬虫层类型](layers) - 三种层的详细说明
- [爬取节点](nodes) - Node 的执行逻辑
- [智能剪枝](pruning) - SequentialLayer 的剪枝机制
- [领域服务](services) - NewsLinkCrawlService 接口
