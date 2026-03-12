"""
触发器层包

职责：
- 定义统一的触发器接口
- 提供多种触发方式（手动、API、定时任务、消息队列）
- 解耦触发逻辑和业务逻辑

可用触发器：
- BaseTrigger: 触发器基类
- ManualTrigger: 手动触发器（命令行）
- APITrigger: HTTP API 触发器（需要 fastapi）
- SchedulerTrigger: 定时任务触发器（需要 apscheduler）
- MessageQueueTrigger: 消息队列触发器（TODO）

使用示例：
    from v1.DDD.trigger import ManualTrigger
    from v1.DDD.app.src.main.DI.container import AppContainer

    container = AppContainer()
    trigger = ManualTrigger(container)
    await trigger.run()
"""

from v1.DDD.trigger.base_trigger import (
    BaseTrigger,
    ManualTrigger,
    APITrigger,
    SchedulerTrigger,
    MessageQueueTrigger,
)

__all__ = [
    "BaseTrigger",
    "ManualTrigger",
    "APITrigger",
    "SchedulerTrigger",
    "MessageQueueTrigger",
]
