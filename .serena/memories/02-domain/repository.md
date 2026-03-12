# 仓储接口设计（含事务支持）

> INewsCrawlRepository - 统一仓储接口

## 位置
`domain/repository/base_news_links_crawl_repository.py`

## 接口设计原则

### 方法分类

#### 只读方法（不需要 session 参数）
- 内部创建自己的 session
- 适用于查询操作

#### 写方法（需要 session 参数）
- 接受外部传入的 session
- 参与调用者的事务
- 适用于增删改操作

## 接口方法

### 新闻源元数据查询（只读）

```python
# 不需要 session 参数
async def get_source_by_resource_id(self, resource_id: str) -> NewsSourceMetadata | None
async def get_all_active_sources(self) -> list[NewsSourceMetadata]
async def get_all_sources(self) -> list[NewsSourceMetadata]
```

### 新闻链接操作

#### 去重检查（只读）
```python
async def check_exists_batch(
    self,
    aggregate: NewsLinkBatchAggregate,
) -> NewsLinkBatchAggregate
```

#### 批量保存（事务方法）
```python
async def save_batch(
    self,
    session: AsyncSession,  # ← 需要 session 参数
    aggregate: NewsLinkBatchAggregate,
) -> BatchSaveResult
```

### 健康检查（事务方法）

```python
async def save_health_check_record(
    self,
    session: AsyncSession,  # ← 需要 session 参数
    record: HealthCheckRecordEntity,
) -> None

async def get_recent_health_checks(
    self,
    session: AsyncSession,  # ← 需要 session 参数
    resource_id: str,
    limit: int = 10,
) -> list[HealthCheckRecordEntity]

async def update_source_status_by_health(
    self,
    session: AsyncSession,  # ← 需要 session 参数
    resource_id: str,
    status: NewsSourceStatusVO,
) -> None
```

## 使用示例

### 场景 1：只读操作
```python
# Repository 内部管理 session
source = await repository.get_source_by_resource_id("test_001")
```

### 场景 2：单个写操作
```python
# Service 层管理事务
async with session_factory() as session:
    async with session.begin():
        await repository.save_batch(session, aggregate)
```

### 场景 3：多个写操作（同一事务）
```python
# Service 层管理事务，多个操作共享 session
async with session_factory() as session:
    async with session.begin():
        # 保存检查记录
        await repository.save_health_check_record(session, record)
        
        # 查询最近记录（同一事务中）
        recent = await repository.get_recent_health_checks(session, resource_id, 3)
        
        # 更新状态（同一事务中）
        if need_update(recent):
            await repository.update_source_status_by_health(session, resource_id, status)
        
        # 退出自动 commit
```

## 出参数据类

### BatchSaveResult
```python
@dataclass
class BatchSaveResult:
    saved_count: int                    # 实际写入成功的条数
    skipped_urls: list[str]             # 因 uq_url 冲突跳过的 URL
```

## 设计优势

### 事务边界清晰
- 只读方法：不需要 session，自主管理
- 写方法：需要 session，参与调用者的事务

### 灵活性高
- 可以组合多个 Repository 操作在同一事务中
- Service 层完全控制事务边界

### 符合 DDD
- 仓储抽象数据访问
- 领域层不依赖具体实现

## 相关链接

- [Repository 实现](../../03-infrastructure/repository) - 具体实现
- [事务管理](../../03-infrastructure/transaction) - 事务设计
- [聚合根](../model/aggregate) - NewsLinkBatchAggregate
