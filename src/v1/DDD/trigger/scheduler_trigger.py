"""
定时任务触发器实现

职责：
- 使用 APScheduler 创建定时任务
- 支持 Cron 表达式配置
- 支持动态添加/删除任务

运行方式：
    python -m v1.DDD.trigger.scheduler_trigger

配置示例：
    # 每天凌晨 2 点爬取所有新闻源
    schedule = "0 2 * * *"

    # 每小时爬取指定新闻源
    schedule = "0 * * * *"
    source_ids = ["id_jawapos"]

TODO: 需要安装依赖
    pip install apscheduler
"""

import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime

# TODO: 取消注释以启用 APScheduler
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.cron import CronTrigger

from v1.DDD.app.src.main.DI.container import AppContainer
from v1.DDD.trigger.base_trigger import BaseTrigger

logger = logging.getLogger(__name__)


class SchedulerTrigger(BaseTrigger):
    """
    定时任务触发器

    使用 APScheduler 创建定时爬取任务

    使用示例：
        # 创建容器
        container = AppContainer()

        # 创建触发器
        trigger = SchedulerTrigger(container=container)

        # 添加定时任务
        trigger.add_job(
            job_id="crawl_all_daily",
            cron="0 2 * * *",  # 每天凌晨2点
            source_ids=None     # 爬取所有
        )

        # 运行（阻塞）
        await trigger.run()
    """

    def __init__(
        self,
        container: AppContainer,
        timezone: str = "Asia/Shanghai"
    ):
        """
        初始化定时任务触发器

        Args:
            container: 依赖注入容器
            timezone: 时区（默认：Asia/Shanghai）
        """
        super().__init__(container)
        self.timezone = timezone
        self.scheduler = None  # APScheduler 实例
        self.jobs: Dict[str, dict] = {}  # 任务配置缓存
        self.registered_ids: List[str] = []

    async def setup(self) -> None:
        """
        初始化定时任务调度器

        - 创建 APScheduler 实例
        - 加载新闻源配置
        - 添加预定义任务
        """
        logger.info("初始化定时任务调度器...")

        # TODO: 取消注释以启用 APScheduler
        """
        # 创建调度器
        self.scheduler = AsyncIOScheduler(timezone=self.timezone)

        # 加载新闻源配置
        self.registered_ids = await self.load_sources()
        logger.info(f"已加载 {len(self.registered_ids)} 个新闻源")

        # 添加默认任务（可选）
        self._add_default_jobs()
        """

        logger.warning("定时任务触发器需要安装依赖: pip install apscheduler")
        logger.warning("当前为示例代码，需要取消注释以启用")

    def _add_default_jobs(self) -> None:
        """添加默认定时任务（可根据需求配置）"""
        # TODO: 取消注释以启用默认任务
        """
        # 示例1: 每天凌晨2点爬取所有新闻源
        self.add_job(
            job_id="crawl_all_daily",
            cron="0 2 * * *",
            source_ids=None,
            description="每日全量爬取"
        )

        # 示例2: 每小时爬取指定新闻源
        self.add_job(
            job_id="crawl_jawapos_hourly",
            cron="0 * * * *",
            source_ids=["id_jawapos"],
            description="每小时爬取 JawaPos"
        )
        """

    def add_job(
        self,
        job_id: str,
        cron: str,
        source_ids: Optional[List[str]] = None,
        description: str = ""
    ) -> bool:
        """
        添加定时任务

        Args:
            job_id: 任务唯一标识
            cron: Cron 表达式（如 "0 2 * * *" 表示每天凌晨2点）
            source_ids: 要爬取的新闻源 ID 列表，None 表示爬取所有
            description: 任务描述

        Returns:
            是否成功添加

        Cron 表达式格式：
            分钟 小时 日 月 星期
            例如：
            - "0 2 * * *"     每天凌晨2点
            - "0 */2 * * *"   每2小时
            - "0 0 * * 1"     每周一凌晨
            - "0 0 1 * *"     每月1号凌晨
        """
        # TODO: 取消注释以启用任务添加
        """
        try:
            # 解析 Cron 表达式
            minute, hour, day, month, day_of_week = cron.split()

            # 创建触发器
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=self.timezone
            )

            # 添加任务
            self.scheduler.add_job(
                func=self._execute_crawl_job,
                trigger=trigger,
                id=job_id,
                name=description or job_id,
                args=[source_ids],
                replace_existing=True  # 如果已存在则替换
            )

            # 缓存任务配置
            self.jobs[job_id] = {
                "cron": cron,
                "source_ids": source_ids,
                "description": description
            }

            logger.info(f"✓ 添加定时任务: {job_id} ({cron}) - {description}")
            return True

        except Exception as e:
            logger.error(f"✗ 添加定时任务失败: {job_id}, {e}")
            return False
        """

        logger.warning("add_job 方法需要取消注释以启用")
        return False

    def remove_job(self, job_id: str) -> bool:
        """
        删除定时任务

        Args:
            job_id: 任务 ID

        Returns:
            是否成功删除
        """
        # TODO: 取消注释以启用任务删除
        """
        try:
            self.scheduler.remove_job(job_id)
            self.jobs.pop(job_id, None)
            logger.info(f"✓ 删除定时任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"✗ 删除定时任务失败: {job_id}, {e}")
            return False
        """

        logger.warning("remove_job 方法需要取消注释以启用")
        return False

    async def _execute_crawl_job(self, source_ids: Optional[List[str]]) -> None:
        """
        执行爬取任务（由调度器调用）

        Args:
            source_ids: 要爬取的新闻源 ID 列表，None 表示爬取所有
        """
        try:
            start_time = datetime.now()
            logger.info(f"{'='*60}")
            logger.info(f"定时任务开始执行: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}")

            if source_ids:
                # 爬取指定新闻源
                logger.info(f"爬取指定的 {len(source_ids)} 个新闻源")
                await self.crawl_multiple_sources(source_ids)
            else:
                # 爬取所有新闻源
                logger.info(f"爬取所有 {len(self.registered_ids)} 个新闻源")
                await self.crawl_multiple_sources(self.registered_ids)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"{'='*60}")
            logger.info(f"定时任务执行完成: 耗时 {duration:.2f} 秒")
            logger.info(f"{'='*60}")

        except Exception as e:
            logger.error(f"定时任务执行失败: {e}", exc_info=True)

    async def start(self) -> None:
        """
        启动定时任务调度器

        阻塞运行，直到手动停止
        """
        # TODO: 取消注释以启用调度器
        """
        logger.info("启动定时任务调度器...")
        logger.info(f"已配置 {len(self.jobs)} 个定时任务:")

        for job_id, config in self.jobs.items():
            logger.info(f"  - {job_id}: {config['cron']} ({config['description']})")

        # 启动调度器
        self.scheduler.start()

        # 保持运行（阻塞）
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("收到停止信号...")
        """

        logger.warning("start 方法需要取消注释以启用")
        logger.info("模拟调度器运行... (按 Ctrl+C 停止)")

        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("收到停止信号...")

    async def stop(self) -> None:
        """停止定时任务调度器"""
        # TODO: 取消注释以启用调度器停止
        """
        if self.scheduler:
            logger.info("停止定时任务调度器...")
            self.scheduler.shutdown(wait=False)
        """

        logger.info("定时任务调度器已停止")


# ------------------------------------------------------------------
# 运行入口（用于直接启动定时任务服务）
# ------------------------------------------------------------------

async def main():
    """
    运行定时任务触发器

    用于独立启动定时任务服务
    """
    from v1.DDD.app.src.main.application import create_app

    # 创建应用
    app = await create_app()

    try:
        # 创建定时任务触发器
        trigger = SchedulerTrigger(
            container=app.container,
            timezone="Asia/Shanghai"
        )

        # TODO: 添加自定义任务
        # trigger.add_job(...)

        # 运行触发器
        await trigger.run()

    finally:
        # 关闭应用
        await app.shutdown()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("定时任务服务已停止")
