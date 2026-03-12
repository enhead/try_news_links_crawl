# 应用服务（待实现）

> ⚠️ 注意：本文件描述的内容为待实现功能，设计可能调整

## 架构说明

**Application 层定位**：
- Application 层是**启动层**（配置、DI容器）
- **不负责业务编排**

**业务调用流程**：
```
API/Trigger 层 → 直接调用 → Domain 层服务
```

小项目简化，无 case 编排层。

## NewsCrawlApplicationService（待实现）

### 当前状态
**尚未实现**，可能的两种设计方案：

### 方案1：轻量封装（推荐）
仅提供简单封装，方便 API/Trigger 层调用：

```python
class NewsCrawlApplicationService:
    \"\"\"轻量封装，不做编排\"\"\"
    
    def __init__(self, crawl_service: NewsLinkCrawlService):
        self.crawl_service = crawl_service
    
    async def crawl_single_source(self, resource_id: str):
        \"\"\"直接委托给领域服务\"\"\"
        return await self.crawl_service.execute_crawl(resource_id)
```

### 方案2：不需要此类
API/Trigger 层直接从容器获取 Domain 服务：

```python
# API/Trigger 层
@app.post("/crawl/{resource_id}")
async def crawl_endpoint(resource_id: str):
    # 直接获取领域服务
    service = app.container.domain_crawl_service()
    return await service.execute_crawl(resource_id)
```

## 容器配置

```python
class AppContainer(containers.DeclarativeContainer):
    # 领域服务（放在容器中管理）
    domain_crawl_service = providers.Factory(
        NewsLinkCrawlService,
        repository=repository
    )
```

## 相关链接

- [领域服务](../02-domain/crawler/services) - NewsLinkCrawlService
- [依赖注入](di_container) - 容器注册
- [待办清单](../06-tasks/pending) - 实现任务
