"""NewsSourceHealthCheck 数据访问对象"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from v1.DDD.infrastructure.persistent.models import NewsSourceHealthCheckModel, NewsSourceModel


class NewsSourceHealthCheckDAO:
    """
    NewsSourceHealthCheck 数据访问对象（无状态）

    设计说明：
    - 不持有 session，每个方法接受 session 参数
    - 可以在 Repository 中复用同一个实例
    - 纯粹的数据库操作封装
    """

    async def insert(self, session: AsyncSession, record: dict) -> int:
        """
        插入健康检查记录

        Args:
            session: 数据库会话
            record: 记录数据字典

        Returns:
            插入的记录 ID
        """
        model = NewsSourceHealthCheckModel(**record)
        session.add(model)
        await session.flush()
        return model.id

    async def find_recent_by_resource_id(
        self, session: AsyncSession, resource_id: str, limit: int = 3
    ) -> list[NewsSourceHealthCheckModel]:
        """
        查询指定新闻源最近的健康检查记录

        Args:
            session: 数据库会话
            resource_id: 新闻源标识
            limit: 查询数量限制

        Returns:
            健康检查记录模型列表，按时间倒序
        """
        stmt = (
            select(NewsSourceHealthCheckModel)
            .where(NewsSourceHealthCheckModel.resource_id == resource_id)
            .order_by(NewsSourceHealthCheckModel.checked_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_source_status(
        self, session: AsyncSession, resource_id: str, status: int
    ) -> int:
        """
        更新新闻源的状态

        Args:
            session: 数据库会话
            resource_id: 新闻源标识
            status: 新状态值

        Returns:
            受影响的行数
        """
        stmt = (
            update(NewsSourceModel)
            .where(NewsSourceModel.resource_id == resource_id)
            .values(status=status)
        )
        result = await session.execute(stmt)
        return result.rowcount
