# 智能剪枝机制

> SequentialLayer 的自动停止条件

## 剪枝的必要性

### 问题
新闻列表翻页爬取时，如何判断何时停止？
- 硬编码最大页数？→ 不灵活，可能漏爬或浪费
- 一直爬到 404？→ 浪费资源

### 解决方案
智能剪枝：根据爬取结果动态判断是否继续

## 两种剪枝条件

### 1. 连续空页剪枝

**触发条件**：
连续 N 页（默认 3 页）没有发现任何新链接

**适用场景**：
- 新闻源已经没有更多内容
- 翻页到了末尾

**示例**：
```
Page 1: 找到 20 条新链接 → 继续
Page 2: 找到 15 条新链接 → 继续
Page 3: 找到 0 条新链接   → 计数器 +1
Page 4: 找到 0 条新链接   → 计数器 +2
Page 5: 找到 0 条新链接   → 计数器 +3，停止爬取
```

### 2. 连续重复页剪枝

**触发条件**：
连续 N 页（默认 3 页）的所有链接都已存在（100%重复）

**适用场景**：
- 增量爬取时，遇到历史数据
- 新闻源没有新内容

**示例**：
```
Page 1: 20 条新链接 / 20 条总链接 (0% 重复)   → 继续
Page 2: 5 条新链接 / 20 条总链接 (75% 重复)  → 继续
Page 3: 0 条新链接 / 20 条总链接 (100% 重复) → 计数器 +1
Page 4: 0 条新链接 / 20 条总链接 (100% 重复) → 计数器 +2
Page 5: 0 条新链接 / 20 条总链接 (100% 重复) → 计数器 +3，停止爬取
```

## 实现机制

### PruneState（剪枝状态）

**维护的状态**：
- `consecutive_empty_pages` - 连续空页计数
- `consecutive_duplicate_pages` - 连续重复页计数
- `empty_threshold` - 空页阈值（默认 3）
- `duplicate_threshold` - 重复页阈值（默认 3）

**更新逻辑**：
```python
class PruneState:
    def update(self, result: CrawlNodeResultEntity):
        # 更新空页计数
        if result.new_count == 0 and result.duplicate_count == 0:
            self.consecutive_empty_pages += 1
        else:
            self.consecutive_empty_pages = 0
        
        # 更新重复页计数
        if result.new_count == 0 and result.duplicate_count > 0:
            self.consecutive_duplicate_pages += 1
        else:
            self.consecutive_duplicate_pages = 0
    
    def should_stop(self) -> bool:
        return (
            self.consecutive_empty_pages >= self.empty_threshold
            or self.consecutive_duplicate_pages >= self.duplicate_threshold
        )
```

### SequentialLayer 集成

**位置**：`domain/service/single_news_link_crawl/crawl_layer/impl/sequential_layer.py`

**执行流程**：
```python
class SequentialLayer:
    async def execute(self, factor):
        prune_state = PruneState()
        current = self.start
        
        while True:
            params = {**factor.params, self.param_name: current}
            
            # 创建节点并执行
            node = DefaultCrawlNode(self.context)
            result = await node.execute(params)
            
            # 更新剪枝状态
            prune_state.update(result)
            
            # 检查是否停止
            if prune_state.should_stop():
                break
            
            current += self.step
        
        return crawl_result
```

## 配置参数

### 默认值
```python
empty_threshold = 3       # 连续 3 页为空
duplicate_threshold = 3   # 连续 3 页全部重复
```

### 自定义配置
```python
{
    "type": "sequential",
    "param_name": "page",
    "start": 1,
    "step": 1,
    "prune_config": {
        "empty_threshold": 5,      # 自定义为 5 页
        "duplicate_threshold": 5
    }
}
```

## 剪枝效果

### 性能提升
- **减少无效请求**：及时停止，不浪费资源
- **加快爬取速度**：避免爬取大量重复或空页

### 数据完整性
- **不会漏爬**：只在连续多页满足条件时停止
- **增量爬取友好**：遇到历史数据自动停止

## 边界情况

### 新闻源间歇性为空
```
Page 1: 20 条新链接
Page 2: 0 条        → 计数器 +1
Page 3: 15 条新链接 → 计数器重置为 0
Page 4: 0 条        → 计数器 +1
...
```
✅ 剪枝机制正确处理：计数器在有结果时重置

### 所有页都是重复
```
Page 1: 0 条新链接, 20 条重复 → 计数器 +1
Page 2: 0 条新链接, 20 条重复 → 计数器 +2
Page 3: 0 条新链接, 20 条重复 → 计数器 +3，停止
```
✅ 增量爬取时快速停止，不浪费资源

## 未来优化

### 动态阈值
根据历史数据动态调整阈值

### 更多剪枝策略
- 基于时间的剪枝（超过 N 天的新闻停止）
- 基于链接质量的剪枝

## 相关链接

- [顺序层](layers#sequentiallayer顺序层) - 顺序层详解
- [爬取节点](nodes) - Node 返回结果供剪枝判断
- [执行流程](execution_flow) - 剪枝在流程中的位置
