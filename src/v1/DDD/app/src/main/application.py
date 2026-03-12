"""
应用启动入口
TODO:   这里我没有时间细看，就现在这样吧，还没有测试
职责：
- 初始化依赖容器
- 配置日志
- 提供应用生命周期管理

使用示例：
    from v1.DDD.app.src.main.application import create_app

    async def main():
        app = await create_app()

        # 使用服务
        service = app.container.crawl_service()
        await service.crawl_single_source("sg_straits_times")

        # 关闭应用
        await app.shutdown()
"""

import logging
from typing import Optional

from v1.DDD.app.src.main.DI.container import AppContainer


class Application:
    """
    应用实例

    职责：
    - 持有依赖容器
    - 管理应用生命周期
    """

    def __init__(self, container: AppContainer):
        self.container = container
        self._logger = logging.getLogger(__name__)

    async def shutdown(self):
        """关闭应用，释放所有资源"""
        self._logger.info("正在关闭应用...")

        # 1. 关闭 HTTP 连接池
        try:
            http = self.container.http_adapter()
            if http and hasattr(http, 'close'):
                self._logger.debug("正在关闭 HTTP 连接池...")
                await http.close()
                self._logger.info("✓ HTTP 连接池已关闭")
        except Exception as e:
            self._logger.warning(f"✗ 关闭 HTTP 连接池失败: {e}")

        # 2. 关闭数据库引擎
        try:
            engine = self.container.db_engine()
            if engine:
                self._logger.debug("正在关闭数据库引擎...")
                await engine.dispose()
                self._logger.info("✓ 数据库引擎已关闭")
        except Exception as e:
            self._logger.error(f"✗ 关闭数据库引擎失败: {e}")

        self._logger.info("应用已关闭")


async def create_app(env_file: str = ".env") -> Application:
    """
    创建应用实例

    Args:
        env_file: .env 文件路径

    Returns:
        Application 实例

    Raises:
        FileNotFoundError: .env 文件不存在
        ValueError: 配置错误
    """
    # 1. 创建容器
    container = AppContainer()

    # 2. 加载配置
    config = container.config()

    # 3. 配置日志
    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info(f"应用启动: env={config.env}")
    logger.info(f"数据库: {config.database.host}:{config.database.port}/{config.database.database}")

    # 4. 创建应用实例
    app = Application(container)

    return app
