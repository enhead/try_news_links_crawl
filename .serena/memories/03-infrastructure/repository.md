# Repository 实现（无状态 + 事务支持）

> NewsLinksCrawlRepository - INewsCrawlRepository 的具体实现

## NewsLinksCrawlRepository

### 位置
`infrastructure/persistent/repository/news_links_crawl_repository.py`

### 核心设计

#### 无状态 + DAO 复用
```python
class NewsLinksCrawlRepository(INewsCrawlRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory
        
        # ✅ 在 __init__ 中创建 DAO 实例（DAO 无状态，可复用）
        self._news_link_dao = NewsLinkDAO()
        self._news_source_dao = NewsSourceDAO()
        self._health_check_dao = NewsSourceHealthCheckDAO()
    
    # ✅ 只读方法：内部创建 session
    async def get_source_by_resource_id(self, resource_id):
        async with self._session_factory() as session:
            model = await self._news_source_dao.find_by_resource_id(session, resource_id)
            return NewsSourceMapper.to_entity(model) if model else None
    
    # ✅ 写方法：接受外部 session（事务控制）
    async def save_batch(self, session: AsyncSession, aggregate):
        records = NewsLinkMapper.aggregate_to_insert_records(aggregate)
        saved_count = await self._news_link_dao.bulk_insert_ignore(session, records)
        return BatchSaveResult(saved_count=saved_count, skipped_urls=[...])
```

### 实现的接口方法

#### 新闻源查询（只读，内部 session）
- `get_source_by_resource_id(resource_id)` - 根据 ID 查询单个新闻源
- `get_all_active_sources()` - 获取所有活跃源（status=0）
- `get_all_sources()` - 获取所有源

#### 新闻链接操作
- `check_exists_batch(aggregate)` - 批量去重（只读，内部 session）
- `save_batch(session, aggregate)` - 批量保存（事务方法）

#### 健康检查（事务方法）
- `save_health_check_record(session, record)` - 保存健康检查记录
- `get_recent_health_checks(session, resource_id, limit)` - 查询最近检查记录
- `update_source_status_by_health(session, resource_id, status)` - 更新源状态

### 依赖
- `session_factory` - 会话工厂（只读操作使用）
- `NewsSourceDAO` - 新闻源数据访问（实例复用）
- `NewsLinkDAO` - 新闻链接数据访问（实例复用）
- `NewsSourceHealthCheckDAO` - 健康检查数据访问（实例复用）
- `NewsSourceMapper` - ORM → 领域对象转换
- `NewsLinkMapper` - 聚合 → 数据库记录转换
- `NewsSourceHealthCheckMapper` - 健康检查转换

## 设计优势

### 依赖倒置
- Domain 层定义接口
- Infrastructure 层实现接口
- 高层不依赖低层

### Mapper 隔离
- Repository 不直接操作 ORM Model
- 通过 Mapper 转换领域对象

### 批量操作
- `bulk_insert_ignore()` - 批量插入去重
- 提升性能

## 相关链接

- [仓储接口](../02-domain/README#仓储接口) - INewsCrawlRepository
- [DAO 层](dao) - 数据访问对象
