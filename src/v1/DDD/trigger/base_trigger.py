"""
触发层基础接口

职责：
- 定义统一的触发器接口
- 为不同的触发方式（API、定时任务、消息队列）提供抽象基类
- 确保触发器与业务逻辑解耦

设计模式：
- 策略模式：不同的触发策略可以互换
- 模板方法模式：统一的生命周期管理

后续扩展：
1. HTTP API 触发器（FastAPI/Flask）
2. 定时任务触发器（APScheduler）
3. 消息队列触发器（RabbitMQ/Kafka）
4. Webhook 触发器
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
import logging

from v1.DDD.app.src.main.DI.container import AppContainer

logger = logging.getLogger(__name__)


class BaseTrigger(ABC):
    """
    触发器基类

    职责：
    - 定义触发器的生命周期（初始化、启动、停止）
    - 提供统一的应用容器访问接口
    - 抽象具体的触发逻辑

    子类需要实现：
    - setup(): 初始化触发器资源
    - start(): 启动触发器
    - stop(): 停止触发器并清理资源
    """

    def __init__(self, container: AppContainer):
        """
        初始化触发器

        Args:
            container: 依赖注入容器
        """
        self.container = container
        self.app_service = container.news_crawl_application_service()
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """触发器是否正在运行"""
        return self._is_running

    @abstractmethod
    async def setup(self) -> None:
        """
        初始化触发器资源

        在启动前调用，用于：
        - 加载配置
        - 初始化客户端连接
        - 注册路由/任务等
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """
        启动触发器

        开始监听触发事件（HTTP 请求、定时任务、消息等）
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        停止触发器并清理资源

        在应用关闭时调用，用于：
        - 停止监听
        - 关闭连接
        - 释放资源
        """
        pass

    async def run(self) -> None:
        """
        运行触发器（完整生命周期）

        流程：
        1. 初始化资源（setup）
        2. 启动触发器（start）
        3. 等待中断信号
        4. 停止触发器（stop）
        """
        try:
            logger.info(f"初始化触发器: {self.__class__.__name__}")
            await self.setup()

            logger.info(f"启动触发器: {self.__class__.__name__}")
            self._is_running = True
            await self.start()

        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止...")

        except Exception as e:
            logger.error(f"触发器运行异常: {e}", exc_info=True)
            raise

        finally:
            logger.info(f"停止触发器: {self.__class__.__name__}")
            self._is_running = False
            await self.stop()

    # ------------------------------------------------------------------
    # 便捷方法：子类可以直接调用业务逻辑
    # ------------------------------------------------------------------

    async def load_sources(self, module_paths: Optional[str | list[str]] = None) -> list[str]:
        """加载新闻源配置"""
        return await self.app_service.load_all_source_configs(module_paths)

    async def crawl_single_source(self, resource_id: str) -> Any:
        """爬取单个新闻源"""
        return await self.app_service.crawl_single_source(resource_id)

    async def crawl_multiple_sources(self, resource_ids: list[str]) -> list[Any]:
        """爬取多个新闻源"""
        return await self.app_service.crawl_multiple_sources(resource_ids)


class ManualTrigger(BaseTrigger):
    """
    手动触发器（用于测试和直接调用）

    使用场景：
    - 命令行直接运行
    - 单元测试
    - 调试

    示例：
        container = AppContainer()
        trigger = ManualTrigger(container)

        # 方式1：使用 run() 完整生命周期
        await trigger.run()

        # 方式2：手动控制生命周期
        await trigger.setup()
        await trigger.start()
        # ... 执行操作
        await trigger.stop()
    """

    def __init__(
        self,
        container: AppContainer,
        source_ids: Optional[list[str]] = None,
        load_sources: bool = True
    ):
        """
        初始化手动触发器

        Args:
            container: 依赖注入容器
            source_ids: 要爬取的新闻源 ID 列表，None 表示爬取所有
            load_sources: 是否在 setup 时自动加载新闻源配置
        """
        super().__init__(container)
        self.source_ids = source_ids
        self.should_load_sources = load_sources
        self.registered_ids: list[str] = []

    async def setup(self) -> None:
        """初始化：加载新闻源配置"""
        if self.should_load_sources:
            logger.info("加载新闻源配置...")
            self.registered_ids = await self.load_sources()
            logger.info(f"已加载 {len(self.registered_ids)} 个新闻源")

    async def start(self) -> None:
        """启动：执行爬取任务"""
        if self.source_ids:
            # 爬取指定新闻源
            logger.info(f"开始爬取指定的 {len(self.source_ids)} 个新闻源")
            await self.crawl_multiple_sources(self.source_ids)
        elif self.registered_ids:
            # 爬取所有已注册的新闻源
            logger.info(f"开始爬取所有 {len(self.registered_ids)} 个新闻源")
            await self.crawl_multiple_sources(self.registered_ids)
        else:
            logger.warning("没有可爬取的新闻源")

    async def stop(self) -> None:
        """停止：清理资源"""
        logger.info("手动触发器已停止")


# ------------------------------------------------------------------
# 后续扩展预留接口（示例框架）
# ------------------------------------------------------------------

class APITrigger(BaseTrigger):
    """
    API 触发器（HTTP REST API）

    TODO: 后续实现
    - 使用 FastAPI/Flask 创建 HTTP 服务
    - 提供 RESTful API 接口
    - 支持异步请求处理

    API 接口示例：
        POST /api/crawl/single
        POST /api/crawl/batch
        GET  /api/sources
        GET  /api/status
    """

    async def setup(self) -> None:
        """初始化 API 服务器"""
        # TODO: 初始化 FastAPI app
        # TODO: 注册路由
        pass

    async def start(self) -> None:
        """启动 API 服务器"""
        # TODO: 启动 uvicorn server
        pass

    async def stop(self) -> None:
        """停止 API 服务器"""
        # TODO: 关闭服务器
        pass


class SchedulerTrigger(BaseTrigger):
    """
    定时任务触发器

    TODO: 后续实现
    - 使用 APScheduler 创建定时任务
    - 支持 cron 表达式
    - 支持任务持久化

    配置示例：
        # 每天凌晨2点爬取所有新闻源
        schedule = "0 2 * * *"

        # 每小时爬取指定新闻源
        schedule = "0 * * * *"
        source_ids = ["id_jawapos"]
    """

    async def setup(self) -> None:
        """初始化定时任务调度器"""
        # TODO: 初始化 APScheduler
        # TODO: 添加定时任务
        pass

    async def start(self) -> None:
        """启动定时任务"""
        # TODO: 启动 scheduler
        pass

    async def stop(self) -> None:
        """停止定时任务"""
        # TODO: 关闭 scheduler
        pass


class MessageQueueTrigger(BaseTrigger):
    """
    消息队列触发器

    TODO: 后续实现
    - 监听消息队列（RabbitMQ/Kafka）
    - 消费爬取任务消息
    - 支持任务重试和死信队列

    消息格式示例：
        {
            "task_type": "crawl_single",
            "resource_id": "id_jawapos",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """

    async def setup(self) -> None:
        """初始化消息队列连接"""
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
