"""数据库引擎和会话管理"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .settings import MySQLSettings


class DatabaseManager:
    """数据库引擎和会话管理器"""

    def __init__(self, settings: MySQLSettings):
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def init_db(self) -> None:
        """初始化数据库引擎和会话工厂"""
        self._engine = create_async_engine(
            self.settings.url,
            echo=self.settings.echo,
            pool_size=self.settings.pool_size,
            max_overflow=self.settings.max_overflow,
            pool_timeout=self.settings.pool_timeout,
            pool_recycle=self.settings.pool_recycle,
            pool_pre_ping=True,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话（上下文管理器）"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init_db() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        """关闭数据库连接池"""
        if self._engine:
            await self._engine.dispose()
