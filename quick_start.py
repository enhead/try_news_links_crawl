"""
快速启动脚本

用于快速测试新闻爬虫服务

运行方式：
    python quick_start.py
"""

import asyncio
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    """快速启动演示"""
    try:
        logger.info("=" * 60)
        logger.info("新闻爬虫服务 - 快速启动")
        logger.info("=" * 60)

        # 导入应用
        from v1.DDD.app.src.main.application import create_app
        from v1.DDD.trigger import ManualTrigger

        # 创建应用
        logger.info("正在初始化应用...")
        app = await create_app()

        try:
            # 创建手动触发器
            logger.info("正在创建触发器...")
            trigger = ManualTrigger(
                container=app.container,
                source_ids=None,  # 爬取所有新闻源（可以改为 ["id_jawapos"] 测试单个）
                load_sources=True
            )

            # 运行触发器
            logger.info("开始执行爬取...")
            await trigger.run()

            logger.info("=" * 60)
            logger.info("爬取任务已完成！")
            logger.info("=" * 60)

        finally:
            # 关闭应用
            await app.shutdown()

    except FileNotFoundError as e:
        logger.error("配置文件未找到，请检查 .env 文件是否存在")
        logger.error(f"详细错误: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"运行失败: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
        sys.exit(0)
