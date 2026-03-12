"""
新闻爬虫主程序

职责：
- 提供应用启动入口
- 支持直接运行和 CLI 命令行模式
- 集成触发器模式，支持多种触发方式

运行方式：
    # 1. 直接运行（爬取所有已注册的新闻源）
    python -m v1.DDD.app.src.main.main

    # 2. 爬取指定新闻源
    python -m v1.DDD.app.src.main.main --source id_jawapos

    # 3. 爬取多个新闻源
    python -m v1.DDD.app.src.main.main --source id_jawapos,sg_straits_times

    # 4. 只加载配置（不执行爬取）
    python -m v1.DDD.app.src.main.main --list-sources

架构说明：
- 使用触发器模式（Trigger Pattern）实现业务触发
- 当前实现：ManualTrigger（命令行直接触发）
- 后续扩展：APITrigger、SchedulerTrigger、MessageQueueTrigger
"""

import asyncio
import logging
import sys
from typing import Optional

from v1.DDD.app.src.main.application import create_app
from v1.DDD.app.src.main.DI.container import AppContainer
from v1.DDD.trigger.base_trigger import ManualTrigger

logger = logging.getLogger(__name__)


class NewscrawlApplication:
    """
    新闻爬虫应用包装器

    职责：
    - 封装应用生命周期管理
    - 提供爬取操作接口
    - 统一错误处理和日志输出
    """

    def __init__(self, container: AppContainer):
        self.container = container
        self.app_service = container.news_crawl_application_service()

    async def load_sources(self, module_paths: Optional[str | list[str]] = None) -> list[str]:
        """
        加载新闻源配置

        Args:
            module_paths: 模块路径，None 表示从 .env 读取

        Returns:
            已注册的新闻源 ID 列表
        """
        logger.info("=" * 60)
        logger.info("开始加载新闻源配置")
        logger.info("=" * 60)

        registered_ids = await self.app_service.load_all_source_configs(module_paths)

        logger.info(f"✓ 成功加载 {len(registered_ids)} 个新闻源")
        for idx, resource_id in enumerate(registered_ids, 1):
            logger.info(f"  {idx}. {resource_id}")

        return registered_ids

    async def crawl_single(self, resource_id: str) -> bool:
        """
        爬取单个新闻源

        Args:
            resource_id: 新闻源 ID

        Returns:
            是否成功
        """
        logger.info("=" * 60)
        logger.info(f"开始爬取: {resource_id}")
        logger.info("=" * 60)

        try:
            result = await self.app_service.crawl_single_source(resource_id)

            logger.info(f"✓ 爬取完成: {resource_id}")
            logger.info(f"  - 发现链接: {len(result.layer_result.urls_found)} 条")
            logger.info(f"  - 新增链接: {len(result.layer_result.urls_new)} 条")

            return True

        except KeyError:
            logger.error(f"✗ 新闻源未注册: {resource_id}")
            return False
        except ValueError as e:
            logger.error(f"✗ 数据库错误: {resource_id}, {e}")
            return False
        except Exception as e:
            logger.error(f"✗ 爬取失败: {resource_id}, {type(e).__name__}: {e}")
            return False

    async def crawl_multiple(self, resource_ids: list[str]) -> dict[str, bool]:
        """
        爬取多个新闻源

        Args:
            resource_ids: 新闻源 ID 列表

        Returns:
            结果字典 {resource_id: 是否成功}
        """
        logger.info("=" * 60)
        logger.info(f"批量爬取: {len(resource_ids)} 个新闻源")
        logger.info("=" * 60)

        results = {}
        for resource_id in resource_ids:
            success = await self.crawl_single(resource_id)
            results[resource_id] = success

        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        failed_count = len(results) - success_count

        logger.info("=" * 60)
        logger.info(f"批量爬取完成")
        logger.info(f"  - 成功: {success_count} 个")
        logger.info(f"  - 失败: {failed_count} 个")
        logger.info("=" * 60)

        return results

    async def crawl_all(self) -> dict[str, bool]:
        """
        爬取所有已注册的新闻源

        Returns:
            结果字典 {resource_id: 是否成功}
        """
        # 先加载配置
        registered_ids = await self.load_sources()

        if not registered_ids:
            logger.warning("未找到任何已注册的新闻源")
            return {}

        # 爬取所有源
        return await self.crawl_multiple(registered_ids)


async def main_async(
    source_ids: Optional[list[str]] = None,
    list_only: bool = False
):
    """
    异步主函数（使用触发器模式）

    架构优势：
    - 解耦触发逻辑和业务逻辑
    - 统一的生命周期管理
    - 便于后续扩展其他触发方式

    Args:
        source_ids: 指定要爬取的新闻源 ID 列表，None 表示爬取所有
        list_only: 是否只列出新闻源（不执行爬取）
    """
    # 1. 创建应用
    app = await create_app()

    try:
        # 2. 如果只是列出，使用简单模式
        if list_only:
            crawler = NewsrawlApplication(app.container)
            registered_ids = await crawler.load_sources()

            if not registered_ids:
                logger.error("未找到任何新闻源配置，请检查配置文件")
                return

            logger.info("=" * 60)
            logger.info("可用的新闻源列表：")
            for resource_id in registered_ids:
                logger.info(f"  - {resource_id}")
            logger.info("=" * 60)
            return

        # 3. 使用触发器模式执行爬取
        trigger = ManualTrigger(
            container=app.container,
            source_ids=source_ids,
            load_sources=True
        )

        # 4. 运行触发器（完整生命周期）
        await trigger.run()

    except Exception as e:
        logger.error(f"应用运行失败: {type(e).__name__}: {e}", exc_info=True)
        raise

    finally:
        # 5. 关闭应用
        await app.shutdown()


def main():
    """
    同步主函数（CLI 入口）

    解析命令行参数并调用异步主函数
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="新闻爬虫应用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 爬取所有新闻源
  python -m v1.DDD.app.src.main.main

  # 爬取指定新闻源
  python -m v1.DDD.app.src.main.main --source id_jawapos

  # 爬取多个新闻源（逗号分隔）
  python -m v1.DDD.app.src.main.main --source id_jawapos,sg_straits_times

  # 列出所有可用新闻源
  python -m v1.DDD.app.src.main.main --list-sources
        """
    )

    parser.add_argument(
        "--source",
        "-s",
        type=str,
        help="指定要爬取的新闻源 ID（多个用逗号分隔）",
    )

    parser.add_argument(
        "--list-sources",
        "-l",
        action="store_true",
        help="列出所有可用的新闻源（不执行爬取）",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别（默认：INFO）",
    )

    args = parser.parse_args()

    # 设置日志级别
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 解析新闻源 ID
    source_ids = None
    if args.source:
        source_ids = [s.strip() for s in args.source.split(",") if s.strip()]

    # 运行异步主函数
    try:
        asyncio.run(main_async(
            source_ids=source_ids,
            list_only=args.list_sources
        ))
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=False)  # 不打印堆栈，因为已经在 main_async 中打印了
        sys.exit(1)


if __name__ == "__main__":
    main()
