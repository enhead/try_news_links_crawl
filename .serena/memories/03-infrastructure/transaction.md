# 事务管理设计

> 基于 SQLAlchemy Session 的事务管理模式

## 核心设计原则

### Session Per Request（每请求一个会话）

```
架构链路：
Service 层（事务边界）
  ↓ 创建 session
  ├─ async with session.begin()  ← 事务开始
  ├─ Repository(session)          ← 传递共享 session
  │   ├─ DAO_1(session)          ← 参与事务
  │   └─ DAO_2(session)          ← 参与事务
  ├─ session.commit()            ← 自动提交
  └─ session.rollback()          ← 异常时自动回滚
```

### 三大原则

1. **事务边界在服务层**
   - Service 控制 `begin()` / `commit()` / `rollback()`
   - 明确的事务生命周期

2. **Repository 无状态**
   - 不持有任何资源
   - 只接受 session 参数

3. **Session 作为工作单元**
   - 一个 session 跟踪所有领域对象变更
   - 多个 Repository/DAO 操作在同一事务中

## 分层职责

| 层次 | 职责 | 事务管理 |
|------|------|----------|
| **Service 层** | 业务编排 + 事务边界 | ✅ 创建/提交/回滚 session |
| **Repository 层** | 聚合持久化 | ❌ 接受 session 参数，不管理事务 |
| **DAO 层** | 原子 SQL 操作 | ❌ 接受 session 参数，不管理事务 |

## 实现示例

### Service 层（事务管理）

```python
class NewsSourceHealthCheckService:
    def __init__(self, session_factory, repository, http_adapter):
        self._session_factory = session_factory
        self._repository = repository
        self._http_adapter = http_adapter
    
    async def check_source_health(self, source_config):
        # 1-4: 业务逻辑（不涉及数据库）
        record = await self._perform_health_check(source_config)
        
        # 5-6: 【事务】保存记录 + 更新状态
        async with self._session_factory() as session:
            async with session.begin():  # ← 事务边界
                # 保存健康检查记录
                await self._repository.save_health_check_record(session, record)
                
                # 查询最近记录
                recent = await self._repository.get_recent_health_checks(
                    session, resource_id, limit=3
                )
                
                # 更新源状态
                if all_failed(recent):
                    await self._repository.update_source_status_by_health(
                        session, resource_id, status
                    )
                # 退出自动 commit，异常自动 rollback
        
        return record
```

### Repository 层（无状态）

```python
class NewsLinksCrawlRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._health_check_dao = NewsSourceHealthCheckDAO()
    
    # ✅ 写方法：接受 session 参数（事务方法）
    async def save_health_check_record(
        self, session: AsyncSession, record: HealthCheckRecordEntity
    ):
        insert_dict = NewsSourceHealthCheckMapper.to_insert_dict(record)
        await self._health_check_dao.insert(session, insert_dict)
    
    # ✅ 只读方法：内部创建 session
    async def get_source_by_resource_id(self, resource_id):
        async with self._session_factory() as session:
            model = await self._news_source_dao.find_by_resource_id(session, resource_id)
            return NewsSourceMapper.to_entity(model) if model else None
```

### DAO 层（无状态）

```python
class NewsSourceHealthCheckDAO:
    """完全无状态，不持有任何资源"""
    
    async def insert(self, session: AsyncSession, record: dict):
        model = NewsSourceHealthCheckModel(**record)
        session.add(model)
        await session.flush()
        return model.id
```

## 事务场景

### 场景 1：单表操作（无需显式事务）
```python
# Repository 内部管理 session
result = await repository.get_source_by_resource_id("test_001")
```

### 场景 2：多表事务操作
```python
# Service 层管理事务
async with session_factory() as session:
    async with session.begin():
        await repository.save_health_check_record(session, record)
        await repository.update_source_status(session, resource_id, status)
```

### 场景 3：跨 Repository 事务
```python
async with session_factory() as session:
    async with session.begin():
        await repository_1.save_xxx(session, data1)
        await repository_2.save_yyy(session, data2)
```

## 设计优势

### 符合企业级最佳实践
- ✅ SQLAlchemy 官方推荐模式
- ✅ Spring `@Transactional` 同样思想
- ✅ Django ORM 事务装饰器

### 架构优势
- ✅ 事务边界清晰（在服务层）
- ✅ Repository 无状态（线程安全）
- ✅ 易于测试（Mock session）
- ✅ 符合 SOLID 原则

### DDD 契合度
- ✅ 聚合根完整性保证（事务边界）
- ✅ 仓储模式正确实现
- ✅ 领域服务编排业务逻辑

## 相关链接

- [DAO 层](dao) - 无状态设计
- [Repository 层](repository) - 无状态 + 事务支持
- [DI 容器](../04-application/di_container) - session_factory 注入
