# 触发器系统

**最后更新**: 2026-03-11

## 概述

触发器系统是应用层的核心组件，负责将不同的触发方式（命令行、HTTP API、定时任务、消息队列）与业务逻辑解耦。

**设计模式**：
- **策略模式**：不同触发策略可互换
- **模板方法模式**：统一的生命周期管理

**核心优势**：
- ✅ 解耦触发方式和业务逻辑
- ✅ 统一的生命周期管理（setup/start/stop/run）
- ✅ 易于扩展新的触发方式
- ✅ 便于测试和调试

## 架构图

```
┌──────────────────────────────────────────────────────────┐
│                    BaseTrigger (抽象基类)                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │  职责：                                            │  │
│  │  - 持有 AppContainer（依赖注入）                  │  │
│  │  - 提供统一的生命周期管理                         │  │
│  │  - 提供便捷方法访问应用服务                       │  │
│  │                                                    │  │
│  │  抽象方法：                                        │  │
│  │  - async setup(): 初始化资源                      │  │
│  │  - async start(): 启动触发器                      │  │
│  │  - async stop(): 停止并清理资源                   │  │
│  │                                                    │  │
│  │  模板方法：                                        │  │
│  │  - async run(): 完整生命周期                      │  │
│  │      1. setup()                                   │  │
│  │      2. start()                                   │  │
│  │      3. 等待中断                                  │  │
│  │      4. stop()                                    │  │
│  └────────────────────────────────────────────────────┘  │
└────────────┬─────────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────┬──────────────┐
    │                 │            │              │
┌───▼────┐    ┌──────▼─────┐  ┌──▼─────┐  ┌─────▼──────┐
│ Manual │    │    API     │  │Scheduler│  │   Queue    │
│Trigger │    │  Trigger   │  │ Trigger│  │  Trigger   │
│  ✅    │    │    ⚠️      │  │   ⚠️   │  │    📋      │
└────────┘    └────────────┘  └────────┘  └────────────┘
  已实现         框架就绪      框架就绪       待实现
```

**图例**：
- ✅ 已完整实现并可用
- ⚠️ 框架已就绪，需安装依赖
- 📋 接口已预留，待实现

## 触发器基类（BaseTrigger）

**文件**: `src/v1/DDD/trigger/base_trigger.py`

### 核心设计

```python
class BaseTrigger(ABC):
    def __init__(self, container: AppContainer):
        self.container = container
        self.app_service = container.news_crawl_application_service()
        self._is_running = False
    
    @abstractmethod
    async def setup(self) -> None:
        """初始化触发器资源"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """启动触发器"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止触发器并清理资源"""
        pass
    
    async def run(self) -> None:
        """完整生命周期（模板方法）"""
        try:
            await self.setup()
            self._is_running = True
            await self.start()
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            self._is_running = False
            await self.stop()
```

### 便捷方法

基类提供了访问应用服务的便捷方法：

```python
# 加载新闻源配置
async def load_sources(
    self,
    module_paths: Optional[str | list[str]] = None
) -> list[str]:
    return await self.app_service.load_all_source_configs(module_paths)

# 爬取单个新闻源
async def crawl_single_source(self, resource_id: str) -> Any:
    return await self.app_service.crawl_single_source(resource_id)

# 爬取多个新闻源
async def crawl_multiple_sources(self, resource_ids: list[str]) -> list[Any]:
    return await self.app_service.crawl_multiple_sources(resource_ids)
```

## 已实现触发器

### 1. ManualTrigger（手动触发器）✅

**状态**: 已完整实现

**使用场景**：
- 命令行直接运行
- 单元测试
- 调试和开发

**核心代码**：
```python
class ManualTrigger(BaseTrigger):
    def __init__(
        self,
        container: AppContainer,
        source_ids: Optional[list[str]] = None,
        load_sources: bool = True
    ):
        super().__init__(container)
        self.source_ids = source_ids
        self.should_load_sources = load_sources
        self.registered_ids: list[str] = []
    
    async def setup(self) -> None:
        """加载新闻源配置"""
        if self.should_load_sources:
            self.registered_ids = await self.load_sources()
    
    async def start(self) -> None:
        """执行爬取任务"""
        if self.source_ids:
            await self.crawl_multiple_sources(self.source_ids)
        elif self.registered_ids:
            await self.crawl_multiple_sources(self.registered_ids)
    
    async def stop(self) -> None:
        """清理资源"""
        logger.info("手动触发器已停止")
```

**使用示例**：
```python
# 方式1：使用 run() 完整生命周期
app = await create_app()
trigger = ManualTrigger(
    container=app.container,
    source_ids=["id_jawapos"],
    load_sources=True
)
await trigger.run()
await app.shutdown()

# 方式2：手动控制生命周期
trigger = ManualTrigger(app.container)
await trigger.setup()
await trigger.start()
# ... 执行其他操作
await trigger.stop()
```

**CLI集成**：
```bash
# 爬取所有新闻源
python -m v1.DDD.app.src.main.main

# 爬取指定新闻源
python -m v1.DDD.app.src.main.main --source id_jawapos

# 爬取多个新闻源
python -m v1.DDD.app.src.main.main --source id_jawapos,sg_straits_times
```

## 框架已就绪触发器

### 2. APITrigger（API触发器）⚠️

**状态**: 框架已就绪，需安装依赖

**文件**: `src/v1/DDD/trigger/api_trigger.py`

**依赖**：
```bash
pip install fastapi uvicorn pydantic
```

**使用场景**：
- 通过 HTTP REST API 触发爬取
- 外部系统集成
- Web管理界面
- 分布式调度系统

**API接口设计**：
```
POST /api/v1/crawl/single
  Body: {"resource_id": "id_jawapos"}
  返回: 爬取结果

POST /api/v1/crawl/batch
  Body: {"resource_ids": ["id_jawapos", "sg_straits_times"]}
  返回: 批量爬取结果

POST /api/v1/crawl/all
  返回: 所有新闻源爬取结果

GET /api/v1/sources
  返回: 所有可用新闻源列表

GET /api/v1/health
  返回: 服务健康状态
```

**实现框架**：
```python
class APITrigger(BaseTrigger):
    async def setup(self) -> None:
        """初始化 FastAPI app，注册路由"""
        # TODO: 初始化 FastAPI app
        # TODO: 注册路由
        pass
    
    async def start(self) -> None:
        """启动 uvicorn server"""
        # TODO: 启动 uvicorn
        pass
    
    async def stop(self) -> None:
        """关闭服务器"""
        # TODO: 关闭服务器
        pass
```

**启用步骤**：
1. 安装依赖：`pip install fastapi uvicorn`
2. 编辑 `trigger/api_trigger.py`
3. 取消注释 TODO 代码块
4. 运行：`python -m v1.DDD.trigger.api_trigger`
5. 访问文档：`http://localhost:8000/docs`

**使用示例**：
```bash
# 启动API服务
python -m v1.DDD.trigger.api_trigger

# 调用API
curl -X POST http://localhost:8000/api/v1/crawl/single \
  -H "Content-Type: application/json" \
  -d '{"resource_id": "id_jawapos"}'
```

### 3. SchedulerTrigger（定时任务触发器）⚠️

**状态**: 框架已就绪，需安装依赖

**文件**: `src/v1/DDD/trigger/scheduler_trigger.py`

**依赖**：
```bash
pip install apscheduler
```

**使用场景**：
- 定时自动爬取（每天凌晨、每小时）
- 周期性任务调度
- 无人值守运行
- 生产环境部署

**Cron表达式示例**：
```python
"0 2 * * *"     # 每天凌晨2点
"0 */2 * * *"   # 每2小时
"0 0 * * 1"     # 每周一凌晨
"0 0 1 * *"     # 每月1号凌晨
"*/30 * * * *"  # 每30分钟
```

**实现框架**：
```python
class SchedulerTrigger(BaseTrigger):
    async def setup(self) -> None:
        """初始化 APScheduler，添加定时任务"""
        # TODO: 初始化 APScheduler
        # TODO: 添加定时任务
        pass
    
    async def start(self) -> None:
        """启动 scheduler"""
        # TODO: 启动 scheduler
        pass
    
    async def stop(self) -> None:
        """关闭 scheduler"""
        # TODO: 关闭 scheduler
        pass
```

**启用步骤**：
1. 安装依赖：`pip install apscheduler`
2. 编辑 `trigger/scheduler_trigger.py`
3. 取消注释 TODO 代码块
4. 配置 Cron 表达式
5. 运行：`python -m v1.DDD.trigger.scheduler_trigger`

**配置示例**：
```python
# 在 _add_default_jobs() 方法中配置
self.add_job(
    job_id="crawl_all_daily",
    cron="0 2 * * *",     # 每天凌晨2点
    source_ids=None,      # 爬取所有新闻源
    description="每日全量爬取"
)

self.add_job(
    job_id="crawl_jawapos_hourly",
    cron="0 * * * *",     # 每小时
    source_ids=["id_jawapos"],
    description="每小时爬取 JawaPos"
)
```

## 待实现触发器

### 4. MessageQueueTrigger（消息队列触发器）📋

**状态**: 接口已预留，待实现

**文件**: `src/v1/DDD/trigger/base_trigger.py`（预留接口）

**使用场景**：
- 基于消息队列的异步触发
- 分布式爬虫集群
- 任务重试和死信队列
- 高吞吐量场景

**技术选型**：
- RabbitMQ（推荐）
- Kafka
- Redis Streams
- AWS SQS / Azure Service Bus

**消息格式示例**：
```json
{
    "task_type": "crawl_single",
    "resource_id": "id_jawapos",
    "timestamp": "2024-01-01T00:00:00Z",
    "priority": 1,
    "retry_count": 0
}
```

**实现框架**：
```python
class MessageQueueTrigger(BaseTrigger):
    async def setup(self) -> None:
        """连接到 MQ，声明队列"""
        # TODO: 连接到 MQ
        # TODO: 声明队列
        pass
    
    async def start(self) -> None:
        """开始消费消息"""
        # TODO: 启动消费者
        pass
    
    async def stop(self) -> None:
        """停止消费并关闭连接"""
        # TODO: 停止消费者
        # TODO: 关闭连接
        pass
```

**实现步骤**：
1. 选择 MQ 技术（RabbitMQ / Kafka）
2. 编辑 `base_trigger.py` 中的 `MessageQueueTrigger`
3. 实现 `setup()`, `start()`, `stop()`
4. 定义消息格式
5. 实现消息消费逻辑
6. 添加错误重试机制

## 生命周期管理

### 统一生命周期（run方法）

所有触发器共享统一的生命周期：

```python
async def run(self) -> None:
    try:
        # 阶段1: 初始化资源
        logger.info("初始化触发器...")
        await self.setup()
        
        # 阶段2: 启动触发器
        logger.info("启动触发器...")
        self._is_running = True
        await self.start()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
        
    except Exception as e:
        logger.error(f"触发器运行异常: {e}", exc_info=True)
        raise
        
    finally:
        # 阶段3: 停止并清理
        logger.info("停止触发器...")
        self._is_running = False
        await self.stop()
```

### 各阶段职责

**setup()阶段**：
- 加载配置
- 初始化客户端连接
- 注册路由/任务/队列
- 验证依赖可用性

**start()阶段**：
- 启动监听（HTTP服务器/调度器/消费者）
- 开始处理请求/任务/消息
- 阻塞直到中断

**stop()阶段**：
- 停止监听
- 关闭客户端连接
- 释放资源
- 记录日志

## 使用模式

### 模式1：完整生命周期

**适用场景**: 大多数情况

```python
app = await create_app()
trigger = ManualTrigger(app.container, source_ids=["id_jawapos"])
try:
    await trigger.run()  # 自动管理 setup/start/stop
finally:
    await app.shutdown()
```

### 模式2：手动控制

**适用场景**: 测试、调试、特殊需求

```python
app = await create_app()
trigger = ManualTrigger(app.container)
try:
    await trigger.setup()
    # 可以在 start 前做其他操作
    await trigger.start()
    # 可以在 stop 前做其他操作
finally:
    await trigger.stop()
    await app.shutdown()
```

### 模式3：触发器组合

**适用场景**: 生产环境（API + 定时任务）

```python
app = await create_app()

# 启动 API 触发器（后台）
api_trigger = FastAPITrigger(app.container, port=8000)
asyncio.create_task(api_trigger.run())

# 启动定时任务触发器（阻塞）
scheduler = SchedulerTrigger(app.container)
await scheduler.run()

# 优雅关闭
await app.shutdown()
```

## 扩展触发器

### 添加新触发器步骤

1. **创建文件**：`src/v1/DDD/trigger/your_trigger.py`

2. **继承基类**：
```python
from v1.DDD.trigger.base_trigger import BaseTrigger

class YourTrigger(BaseTrigger):
    def __init__(self, container: AppContainer, **kwargs):
        super().__init__(container)
        # 自定义初始化参数
        self.your_param = kwargs.get('your_param')
```

3. **实现抽象方法**：
```python
    async def setup(self) -> None:
        """初始化你的资源"""
        # 加载配置
        # 初始化客户端
        # 注册路由/任务
        pass
    
    async def start(self) -> None:
        """启动触发器"""
        # 开始监听
        # 处理请求/任务/消息
        pass
    
    async def stop(self) -> None:
        """停止并清理"""
        # 停止监听
        # 关闭连接
        # 释放资源
        pass
```

4. **使用触发器**：
```python
app = await create_app()
trigger = YourTrigger(app.container, your_param="value")
await trigger.run()
await app.shutdown()
```

### 触发器最佳实践

✅ **DO**：
- 在 `setup()` 中验证依赖和配置
- 在 `start()` 中阻塞等待中断信号
- 在 `stop()` 中优雅关闭所有资源
- 使用 `logger` 记录关键步骤
- 捕获并记录异常，但允许向上传播

❌ **DON'T**：
- 不要在 `__init__` 中执行异步操作
- 不要在 `setup()` 中启动长期运行的任务
- 不要在 `start()` 中返回（除非触发器立即完成）
- 不要在 `stop()` 中抛出异常
- 不要直接访问领域层或基础设施层（通过 `app_service`）

## 相关记忆

- **应用层概览** → `04-application/README`
- **DI容器** → `04-application/di_container`
- **生命周期管理** → `04-application/lifecycle`
- **应用服务** → `04-application/services`