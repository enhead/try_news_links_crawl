# 爬虫层类型

> 三种层类型实现：枚举层、映射层、顺序层

## 层的概念

每层负责一个维度的参数遍历，层可以嵌套形成树状结构。

## EnumerableLayer（枚举层）

### 用途
遍历固定的值列表

### 使用场景
- 遍历栏目列表：`["politics", "tech", "sports"]`
- 遍历地区列表：`["north", "south", "east", "west"]`

### 特点
- 可以嵌套下一层
- 参数值固定不变

### 配置示例
```python
{
    "type": "enumerable",
    "param_name": "category",
    "values": ["politics", "tech", "sports"]
}
```

### 执行逻辑
```python
for value in values:
    params[param_name] = value
    if next_layer:
        next_layer.execute(params)
```

## MappingLayer（映射层）

### 用途
根据依赖关系动态生成参数

### 使用场景
- 根据一级栏目映射到对应的二级栏目
- 根据地区映射到对应的城市

### 特点
- 支持一对多映射关系
- 依赖上层参数动态生成值
- 可以嵌套下一层

### 配置示例
```python
{
    "type": "mapping",
    "param_name": "subcategory",
    "depends_on": "category",
    "mapping": {
        "politics": ["domestic", "international"],
        "tech": ["ai", "blockchain", "mobile"],
        "sports": ["football", "basketball"]
    }
}
```

### 执行逻辑
```python
depend_value = params[depends_on]
for value in mapping[depend_value]:
    params[param_name] = value
    if next_layer:
        next_layer.execute(params)
```

## SequentialLayer（顺序层）

### 用途
叶子层，负责翻页爬取

### 使用场景
- 新闻列表翻页：page=1, 2, 3, ...
- 时间范围遍历：date=2024-01-01, 2024-01-02, ...

### 特点
- **不能嵌套下一层**（叶子层）
- 从 `start` 开始，每次增加 `step`
- 支持智能剪枝（见 [pruning](pruning)）

### 配置示例
```python
{
    "type": "sequential",
    "param_name": "page",
    "start": 1,
    "step": 1
}
```

### 执行逻辑
```python
current = start
while not should_stop:
    params[param_name] = current
    node = create_node()
    result = node.execute(params)
    
    # 智能剪枝检查
    if is_empty_or_duplicate(result):
        should_stop = True
    
    current += step
```

## 层的嵌套

### 示例：三层嵌套
```
EnumerableLayer (栏目: politics, tech, sports)
  └─ MappingLayer (子栏目: domestic/international, ai/blockchain, ...)
      └─ SequentialLayer (翻页: page=1, 2, 3, ...)
```

### 参数合并
每层将自己的参数合并到总参数集中，传递给下一层：
```python
# 执行结果示例
params = {
    "category": "politics",      # EnumerableLayer 添加
    "subcategory": "domestic",   # MappingLayer 添加
    "page": 1                    # SequentialLayer 添加
}
```

## 抽象基类

### AbstractCrawlLayer
**位置**：`domain/service/single_news_link_crawl/crawl_layer/abstract_layer.py`

**核心方法**：
- `execute(factor)` - 模板方法，定义执行流程
- `_generate_params()` - 抽象方法，子类实现参数生成

## 工厂创建

### CrawlLayerFactory
**位置**：`domain/service/single_news_link_crawl/crawl_layer/factory/layer_factory.py`

**使用装饰器注册**：
```python
@CrawlLayerFactory.register(LayerType.SEQUENTIAL)
class SequentialLayer(AbstractCrawlLayer):
    ...

# 使用工厂创建
layer = CrawlLayerFactory.build(schema, next_layer, context)
```

**LayerType 枚举**：
- `LayerType.ENUMERABLE` - 枚举层
- `LayerType.MAPPING` - 映射层
- `LayerType.SEQUENTIAL` - 顺序层

## 设计优势

### 组合模式
- 统一的 `execute()` 接口
- 灵活组合，支持任意层级
- 易于扩展新层类型

### 职责单一
- 每层只负责一个维度的参数遍历
- 参数生成与执行逻辑分离

## 相关链接

- [爬取节点](nodes) - 节点执行爬取任务
- [智能剪枝](pruning) - 顺序层的剪枝机制
- [执行流程](execution_flow) - Layer 树的完整执行流程
