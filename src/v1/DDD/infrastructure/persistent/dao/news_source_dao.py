"""NewsSource 数据访问对象"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from v1.DDD.infrastructure.persistent.models import NewsSourceModel


class NewsSourceDAO:
    """
    NewsSource 数据访问对象（无状态）

    设计说明：
    - 不持有 session，每个方法接受 session 参数
    - 可以在 Repository 中复用同一个实例
    - 纯粹的数据库操作封装
    """

    async def find_by_resource_id(
        self, session: AsyncSession, resource_id: str
    ) -> NewsSourceModel | None:
        """
        根据 resource_id 查询新闻源

        Args:
            session: 数据库会话
            resource_id: 新闻源标识

        Returns:
            新闻源模型，不存在则返回 None
        """
        stmt = select(NewsSourceModel).where(NewsSourceModel.resource_id == resource_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_by_status(
        self, session: AsyncSession, status: int
    ) -> list[NewsSourceModel]:
        """
        根据状态查询新闻源列表

        Args:
            session: 数据库会话
            status: 新闻源状态（0-正常 1-停用 2-解析异常）

        Returns:
            新闻源模型列表
        """
        stmt = select(NewsSourceModel).where(NewsSourceModel.status == status)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_all(self, session: AsyncSession) -> list[NewsSourceModel]:
        """
        查询所有新闻源

        Args:
            session: 数据库会话

        Returns:
            新闻源模型列表
        """
        stmt = select(NewsSourceModel)
        result = await session.execute(stmt)
        return list(result.scalars().all())

