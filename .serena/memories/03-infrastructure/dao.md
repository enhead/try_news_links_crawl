# DAO 层设计（无状态）

> Data Access Object - 纯数据库操作，完全无状态

## DAO 命名规范（参照 Java 后端）

### 单条查询
- `find_by_xxx()` → `Model | None`
- 示例：`find_by_resource_id()`, `find_by_id()`

### 列表查询（带条件）
- `find_all_by_xxx()` → `list[Model]`
- 示例：`find_all_by_status()`, `find_all_by_country()`

### 列表查询（无条件）
- `find_all()` → `list[Model]`

### 写操作
- `save()`, `update()`, `delete()`, `bulk_insert_ignore()`

## 核心设计原则

### 完全无状态
- ❌ 不持有 session 成员变量
- ✅ 每个方法接受 `session: AsyncSession` 作为第一个参数
- ✅ 可以在 Repository 中创建一次并复用

### 方法签名示例
```python
class NewsSourceDAO:
    """无状态 DAO"""
    
    # ✅ session 作为方法参数
    async def find_by_resource_id(
        self,
        session: AsyncSession,
        resource_id: str
    ) -> NewsSourceModel | None:
        result = await session.execute(...)
        return result.scalar_one_or_none()
```

## 核心 DAO

### NewsSourceDAO
**位置**：`infrastructure/persistent/dao/news_source_dao.py`

**方法**：
- `find_by_resource_id(session, resource_id)` - 查询单个新闻源
- `find_all_by_status(session, status)` - 按状态查询
- `find_all(session)` - 查询所有

### NewsLinkDAO
**位置**：`infrastructure/persistent/dao/news_link_dao.py`

**方法**：
- `bulk_insert_ignore(session, records)` - 批量插入去重
- `check_urls_exist(session, urls)` - 批量查询链接是否存在

### NewsSourceHealthCheckDAO
**位置**：`infrastructure/persistent/dao/news_source_health_check_dao.py`

**方法**：
- `insert(session, record)` - 插入健康检查记录
- `find_recent_by_resource_id(session, resource_id, limit)` - 查询最近记录
- `update_source_status(session, resource_id, status)` - 更新新闻源状态

## Mapper 模式

### NewsSourceMapper
**位置**：`infrastructure/persistent/mapper/news_source_mapper.py`

**方法**：
- `to_dict(model)` - ORM Model → 字典
- `to_entity(model)` - ORM Model → NewsSourceMetadata
- `to_entity_list(models)` - 批量转换

### NewsLinkMapper
**位置**：`infrastructure/persistent/mapper/news_link_mapper.py`

**方法**：
- `aggregate_to_insert_records(aggregate)` - 聚合 → 插入记录

## 设计原则

### 职责单一
- DAO 只负责数据库操作
- 不包含业务逻辑

### ORM 封装
- 使用 SQLAlchemy 异步 API
- 批量操作优化性能

## 相关链接

- [数据库设计](database) - 表结构
- [Repository](repository) - 使用 DAO
