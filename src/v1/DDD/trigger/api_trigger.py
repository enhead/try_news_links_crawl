"""
FastAPI 触发器实现

职责：
- 提供 HTTP REST API 接口触发爬虫
- 支持同步和异步请求
- 提供状态查询和配置管理接口

运行方式：
    python -m v1.DDD.trigger.api_trigger

API 接口：
    POST /api/v1/crawl/single        - 爬取单个新闻源
    POST /api/v1/crawl/batch         - 批量爬取新闻源
    POST /api/v1/crawl/all           - 爬取所有新闻源
    GET  /api/v1/sources             - 获取所有新闻源列表
    GET  /api/v1/sources/{source_id} - 获取指定新闻源信息
    GET  /api/v1/health              - 健康检查

TODO: 需要安装依赖
    pip install fastapi uvicorn pydantic
"""

import asyncio
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

# TODO: 取消注释以启用 FastAPI
# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel

from v1.DDD.app.src.main.DI.container import AppContainer
from v1.DDD.trigger.base_trigger import BaseTrigger

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 请求/响应数据模型
# ------------------------------------------------------------------

# TODO: 取消注释以启用数据模型
"""
class CrawlSingleRequest(BaseModel):
    '''爬取单个新闻源请求'''
    resource_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "id_jawapos"
            }
        }


class CrawlBatchRequest(BaseModel):
    '''批量爬取新闻源请求'''
    resource_ids: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "resource_ids": ["id_jawapos", "sg_straits_times"]
            }
        }


class CrawlResponse(BaseModel):
    '''爬取响应'''
    success: bool
    message: str
    data: Optional[dict] = None


class SourceInfo(BaseModel):
    '''新闻源信息'''
    resource_id: str
    name: str
    domain: str
    country: str
    language: str
    status: str
"""


# ------------------------------------------------------------------
# FastAPI 触发器实现
# ------------------------------------------------------------------

class FastAPITrigger(BaseTrigger):
    """
    FastAPI 触发器

    提供 HTTP REST API 接口触发爬虫任务

    使用示例：
        # 创建容器
        container = AppContainer()

        # 创建触发器
        trigger = FastAPITrigger(
            container=container,
            host="0.0.0.0",
            port=8000
        )

        # 运行（阻塞）
        await trigger.run()
    """

    def __init__(
        self,
        container: AppContainer,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False
    ):
        """
        初始化 FastAPI 触发器

        Args:
            container: 依赖注入容器
            host: 服务器地址
            port: 服务器端口
            reload: 是否启用热重载（开发模式）
        """
        super().__init__(container)
        self.host = host
        self.port = port
        self.reload = reload
        self.app = None  # FastAPI app 实例
        self.registered_ids: List[str] = []

    async def setup(self) -> None:
        """
        初始化 FastAPI 应用

        - 创建 FastAPI 实例
        - 注册路由
        - 加载新闻源配置
        """
        logger.info("初始化 FastAPI 应用...")

        # TODO: 取消注释以启用 FastAPI
        """
        # 创建 FastAPI app（带生命周期管理）
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 启动时加载配置
            logger.info("加载新闻源配置...")
            self.registered_ids = await self.load_sources()
            logger.info(f"已加载 {len(self.registered_ids)} 个新闻源")
            yield
            # 关闭时清理资源
            logger.info("清理资源...")

        self.app = FastAPI(
            title="新闻爬虫 API",
            description="提供新闻爬虫触发和管理接口",
            version="1.0.0",
            lifespan=lifespan
        )

        # 注册路由
        self._register_routes()
        """

        logger.warning("FastAPI 触发器需要安装依赖: pip install fastapi uvicorn")
        logger.warning("当前为示例代码，需要取消注释以启用")

    def _register_routes(self) -> None:
        """注册所有 API 路由"""
        # TODO: 取消注释以启用路由
        """
        @self.app.get("/")
        async def root():
            return {"message": "新闻爬虫 API 服务运行中"}

        @self.app.get("/api/v1/health")
        async def health_check():
            return {
                "status": "healthy",
                "sources_loaded": len(self.registered_ids)
            }

        @self.app.get("/api/v1/sources")
        async def list_sources():
            '''获取所有新闻源列表'''
            return {
                "success": True,
                "count": len(self.registered_ids),
                "sources": self.registered_ids
            }

        @self.app.post("/api/v1/crawl/single")
        async def crawl_single(request: CrawlSingleRequest, background_tasks: BackgroundTasks):
            '''爬取单个新闻源（异步后台任务）'''
            try:
                # 验证新闻源是否存在
                if request.resource_id not in self.registered_ids:
                    raise HTTPException(
                        status_code=404,
                        detail=f"新闻源未找到: {request.resource_id}"
                    )

                # 添加后台任务
                background_tasks.add_task(
                    self.crawl_single_source,
                    request.resource_id
                )

                return {
                    "success": True,
                    "message": f"爬取任务已提交: {request.resource_id}"
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"爬取失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/crawl/batch")
        async def crawl_batch(request: CrawlBatchRequest, background_tasks: BackgroundTasks):
            '''批量爬取新闻源（异步后台任务）'''
            try:
                # 验证所有新闻源是否存在
                invalid_ids = [
                    rid for rid in request.resource_ids
                    if rid not in self.registered_ids
                ]

                if invalid_ids:
                    raise HTTPException(
                        status_code=404,
                        detail=f"以下新闻源未找到: {invalid_ids}"
                    )

                # 添加后台任务
                background_tasks.add_task(
                    self.crawl_multiple_sources,
                    request.resource_ids
                )

                return {
                    "success": True,
                    "message": f"批量爬取任务已提交: {len(request.resource_ids)} 个新闻源"
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"批量爬取失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/crawl/all")
        async def crawl_all(background_tasks: BackgroundTasks):
            '''爬取所有新闻源（异步后台任务）'''
            try:
                if not self.registered_ids:
                    raise HTTPException(
                        status_code=404,
                        detail="没有可用的新闻源"
                    )

                # 添加后台任务
                background_tasks.add_task(
                    self.crawl_multiple_sources,
                    self.registered_ids
                )

                return {
                    "success": True,
                    "message": f"全量爬取任务已提交: {len(self.registered_ids)} 个新闻源"
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"全量爬取失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        """

    async def start(self) -> None:
        """
        启动 FastAPI 服务器

        使用 uvicorn 运行服务器
        """
        logger.info(f"启动 FastAPI 服务器: http://{self.host}:{self.port}")

        # TODO: 取消注释以启用服务器
        """
        import uvicorn

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            reload=self.reload,
            log_level="info"
        )

        server = uvicorn.Server(config)
        await server.serve()
        """

        logger.warning("FastAPI 服务器需要取消注释以启用")

    async def stop(self) -> None:
        """停止 FastAPI 服务器"""
        logger.info("FastAPI 服务器已停止")


# ------------------------------------------------------------------
# 运行入口（用于直接启动 API 服务）
# ------------------------------------------------------------------

async def main():
    """
    运行 FastAPI 触发器

    用于独立启动 API 服务
    """
    from v1.DDD.app.src.main.application import create_app

    # 创建应用
    app = await create_app()

    try:
        # 创建 API 触发器
        trigger = FastAPITrigger(
            container=app.container,
            host="0.0.0.0",
            port=8000,
            reload=False  # 生产环境设为 False
        )

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
        logger.info("API 服务已停止")
