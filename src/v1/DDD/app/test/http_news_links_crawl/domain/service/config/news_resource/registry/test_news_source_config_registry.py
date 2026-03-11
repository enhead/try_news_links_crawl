"""
NewsSourceConfigRegistry 单元测试

【测试入口】
test_register_config - 测试配置类注册功能
test_register_duplicate_raises_error - 测试重复注册抛出异常
test_register_invalid_class_raises_error - 测试注册非继承类抛出异常
test_get_config_class - 测试获取配置类
test_get_config_class_not_found - 测试获取不存在的配置类
test_create_config_singleton - 测试单例模式配置创建
test_create_config_not_found_in_db - 测试数据库中不存在的配置
test_has_config - 测试检查配置是否存在
test_list_registered - 测试列出已注册配置
test_clear_cache - 测试清除缓存
test_clear_registry - 测试清除注册表

【运行命令】
pytest src/v1/DDD/app/test/http_news_links_crawl/domain/service/config/news_resource/registry/test_news_source_config_registry.py                                        # 运行所有测试
pytest src/v1/DDD/app/test/http_news_links_crawl/domain/service/config/news_resource/registry/test_news_source_config_registry.py::test_register_config -v              # 运行单个测试
pytest src/v1/DDD/app/test/http_news_links_crawl/domain/service/config/news_resource/registry/test_news_source_config_registry.py -v -s                                  # 详细输出

-v 详细输出
-s 显示 print 输出（包括日志和统计信息）
- --log-cli-level=INFO 显示 INFO 级别日志，这里换成debug更详细
"""
"""
 ⚡ 对程序的影响

  1. 模块导入时自动注册

  - ✅ 优点：配置类在模块导入时自动注册，无需手动调用
  - ⚠️ 注意：如果配置类模块未被导入，则不会注册

  2. 全局状态共享

  - 注册表是类级别变量，在整个应用生命周期中全局共享
  - 所有代码都访问同一个注册表实例

  3. 单例模式

  # 首次创建：查数据库 + 实例化 + 缓存
  config1 = await NewsSourceConfigRegistry.create_config("test_source", repo)

  # 后续调用：直接返回缓存实例
  config2 = await NewsSourceConfigRegistry.create_config("test_source", repo)

  assert config1 is config2  # 同一个对象
  - ✅ 优点：节省资源，避免重复实例化
  - ⚠️ 注意：修改配置实例会全局生效

  4. 防御性检查

  - ✅ 重复注册检查：防止同一 resource_id 被重复注册（test_news_source_config_registry.py:156-169）
  - ✅ 类型检查：确保配置类继承 AbstractNewsSourceConfig（test_news_source_config_registry.py:171-178）

  🔍 是否会影响程序？

  一般情况下不会有负面影响，因为：
  1. ✅ 设计良好，有完善的测试覆盖
  2. ✅ 有防御性检查（重复注册、类型检查）
  3. ✅ 单例模式提升性能

  需要注意的场景：
  1. ⚠️ 测试隔离：测试时需要清理注册表（已通过 @pytest.fixture(autouse=True) 自动处理）
  2. ⚠️ 动态重载：如果需要热更新配置，需要手动调用 clear_cache() 或 clear_registry()
  3. ⚠️ 模块导入顺序：确保所有配置类模块在使用前被导入


  📝 使用建议

  当您添加新的新闻源配置时，按以下步骤操作即可：

  # 1. 创建配置类文件：jawapos_config.py
  @NewsSourceConfigRegistry.register("id_jawapos")
  class JawaPosConfig(AbstractNewsSourceConfig):
      ...

  # 2. 在 __init__.py 中导入（触发注册）
  from v1.DDD.app.src.resource.news_source.jawapos_config import JawaPosConfig

  🔒 安全保障

  注册表有多重保护机制：
  - ✅ 防止重复注册（会抛出 ValueError）
  - ✅ 类型检查（必须继承 AbstractNewsSourceConfig）
  - ✅ 单例模式（性能优化）
  - ✅ 测试隔离（自动清理注册表）
"""
import pytest
from unittest.mock import AsyncMock

from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.valobj import NewsSourceStatusVO
from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import INewsCrawlRepository
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import AbstractNewsSourceConfig
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.registry.news_source_config_registry import NewsSourceConfigRegistry
from v1.DDD.domain.http_news_links_crawl.model.entity.response_parse_result_entity import ResponseParseResultEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj.response_parse_result_status_vo import ResponseParseResultStatusVO
from v1.DDD.infrastructure.http.response import Response


class MockNewsSourceConfig(AbstractNewsSourceConfig):
    """Mock 新闻源配置类,用于测试"""

    def __init__(self, metadata: NewsSourceMetadata, layer_schema=None, template_request_config=None):
        """重写初始化方法,简化测试"""
        super().__init__(metadata, layer_schema, template_request_config)
        self.metadata = metadata
        self.layer_schema = layer_schema
        self.template_request_config = template_request_config

    def parse_response(self, response: Response) -> ResponseParseResultEntity:
        """Mock 解析方法"""
        return ResponseParseResultEntity(
            status=ResponseParseResultStatusVO.SUCCESS,
            urls=["https://example.com/news1", "https://example.com/news2"],
            errors=[]
        )

    def extract_category(self, params: dict) -> str:
        """Mock 分类提取方法"""
        return params.get("category", "unknown")


class InvalidConfig:
    """无效的配置类（未继承 AbstractNewsSourceConfig）"""
    pass


class MockRepository(INewsCrawlRepository):
    """Mock 仓储实现"""

    def __init__(self):
        self.sources = {}

    async def get_source_by_resource_id(self, resource_id: str):
        """返回预设的元数据"""
        return self.sources.get(resource_id)

    async def save_health_check_record(self, record):
        pass

    async def get_recent_health_checks(self, resource_id: str, limit: int = 10):
        pass

    async def update_source_status_by_health(self, resource_id: str, status):
        pass

    async def check_exists_batch(self, urls_or_aggregate):
        pass

    async def save_batch(self, aggregate):
        pass

    async def get_all_active_sources(self):
        pass

    async def get_all_sources(self):
        pass


@pytest.fixture(autouse=True)
def clean_registry():
    """每个测试前后清空注册表,确保测试隔离"""
    NewsSourceConfigRegistry.clear_registry()
    yield
    NewsSourceConfigRegistry.clear_registry()


@pytest.fixture
def mock_metadata():
    """Mock 元数据"""
    return NewsSourceMetadata(
        resource_id="test_source",
        name="Test Source",
        domain="example.com",
        url="https://example.com",
        country="US",
        language="en",
        status=NewsSourceStatusVO.NORMAL
    )


@pytest.fixture
def mock_repository(mock_metadata):
    """Mock 仓储"""
    repo = MockRepository()
    repo.sources["test_source"] = mock_metadata
    return repo


def test_register_config():
    """测试配置类注册：验证装饰器注册、类型检查"""
    @NewsSourceConfigRegistry.register("test_source")
    class TestConfig(AbstractNewsSourceConfig):
        def parse_response(self, response):
            return ResponseParseResultEntity(
                status=ResponseParseResultStatusVO.SUCCESS,
                urls=[],
                errors=[]
            )

        def extract_category(self, params):
            return "test"

    # 验证注册成功
    assert NewsSourceConfigRegistry.has_config("test_source")
    assert NewsSourceConfigRegistry.get_config_class("test_source") == TestConfig

    # 验证列表中包含该配置
    registered = NewsSourceConfigRegistry.list_registered()
    assert "test_source" in registered

    print(f"\n[OK] 成功注册配置: test_source")
    print(f"[OK] 已注册配置列表: {registered}")


def test_register_duplicate_raises_error():
    """测试重复注册：验证抛出 ValueError"""
    @NewsSourceConfigRegistry.register("duplicate_source")
    class FirstConfig(MockNewsSourceConfig):
        pass

    # 尝试重复注册
    with pytest.raises(ValueError, match="配置类已注册"):
        @NewsSourceConfigRegistry.register("duplicate_source")
        class SecondConfig(MockNewsSourceConfig):
            pass

    print(f"\n[OK] 重复注册正确抛出 ValueError")


def test_register_invalid_class_raises_error():
    """测试注册无效类：验证类型检查"""
    with pytest.raises(TypeError, match="配置类必须继承 AbstractNewsSourceConfig"):
        @NewsSourceConfigRegistry.register("invalid_source")
        class InvalidClass:
            pass

    print(f"\n[OK] 注册无效类正确抛出 TypeError")


def test_get_config_class():
    """测试获取配置类：验证获取已注册的类"""
    @NewsSourceConfigRegistry.register("get_test_source")
    class GetTestConfig(MockNewsSourceConfig):
        pass

    config_class = NewsSourceConfigRegistry.get_config_class("get_test_source")

    assert config_class == GetTestConfig
    assert issubclass(config_class, AbstractNewsSourceConfig)

    print(f"\n[OK] 成功获取配置类: {config_class.__name__}")


def test_get_config_class_not_found():
    """测试获取不存在的配置类：验证抛出 KeyError"""
    with pytest.raises(KeyError, match="未找到配置类"):
        NewsSourceConfigRegistry.get_config_class("non_existent_source")

    print(f"\n[OK] 获取不存在的配置类正确抛出 KeyError")


@pytest.mark.asyncio
async def test_create_config_singleton(mock_repository, mock_metadata):
    """测试单例模式配置创建：验证单例缓存、数据库查询"""
    @NewsSourceConfigRegistry.register("test_source")
    class SingletonConfig(MockNewsSourceConfig):
        pass

    # 第一次创建
    config1 = await NewsSourceConfigRegistry.create_config("test_source", mock_repository)

    # 验证配置对象
    assert isinstance(config1, SingletonConfig)
    assert config1.metadata == mock_metadata
    assert config1.source_id == "test_source"

    # 第二次创建（应返回缓存）
    config2 = await NewsSourceConfigRegistry.create_config("test_source", mock_repository)

    # 验证单例
    assert config1 is config2

    print(f"\n[OK] 配置对象创建成功: {config1.__class__.__name__}")
    print(f"[OK] 单例验证通过: config1 is config2 = {config1 is config2}")
    print(f"[OK] 元数据: resource_id={config1.source_id}, name={config1.name}")


@pytest.mark.asyncio
async def test_create_config_not_found_in_db(mock_repository):
    """测试数据库中不存在的配置：验证抛出 ValueError"""
    @NewsSourceConfigRegistry.register("db_missing_source")
    class DbMissingConfig(MockNewsSourceConfig):
        pass

    # 数据库中没有这个 resource_id
    with pytest.raises(ValueError, match="数据库中未找到新闻源"):
        await NewsSourceConfigRegistry.create_config("db_missing_source", mock_repository)

    print(f"\n[OK] 数据库中不存在的配置正确抛出 ValueError")


def test_has_config():
    """测试检查配置是否存在：验证存在性检查"""
    @NewsSourceConfigRegistry.register("exists_source")
    class ExistsConfig(MockNewsSourceConfig):
        pass

    assert NewsSourceConfigRegistry.has_config("exists_source") is True
    assert NewsSourceConfigRegistry.has_config("non_existent_source") is False

    print(f"\n[OK] 配置存在性检查正确")


def test_list_registered():
    """测试列出已注册配置：验证返回完整列表"""
    @NewsSourceConfigRegistry.register("source_1")
    class Config1(MockNewsSourceConfig):
        pass

    @NewsSourceConfigRegistry.register("source_2")
    class Config2(MockNewsSourceConfig):
        pass

    @NewsSourceConfigRegistry.register("source_3")
    class Config3(MockNewsSourceConfig):
        pass

    registered = NewsSourceConfigRegistry.list_registered()

    assert len(registered) == 3
    assert set(registered) == {"source_1", "source_2", "source_3"}

    print(f"\n[OK] 已注册配置: {registered}")


@pytest.mark.asyncio
async def test_clear_cache(mock_repository, mock_metadata):
    """测试清除缓存：验证单个清除和全部清除"""
    # 注册并创建两个配置
    @NewsSourceConfigRegistry.register("cache_test_1")
    class CacheConfig1(MockNewsSourceConfig):
        pass

    @NewsSourceConfigRegistry.register("cache_test_2")
    class CacheConfig2(MockNewsSourceConfig):
        pass

    # 添加第二个配置到 mock repository
    mock_metadata_2 = NewsSourceMetadata(
        resource_id="cache_test_2",
        name="Cache Test 2",
        domain="example.com",
        url="https://example.com",
        country="US",
        language="en",
        status=NewsSourceStatusVO.NORMAL
    )
    mock_repository.sources["cache_test_1"] = mock_metadata
    mock_repository.sources["cache_test_2"] = mock_metadata_2

    # 创建配置实例
    config1_before = await NewsSourceConfigRegistry.create_config("cache_test_1", mock_repository)
    config2_before = await NewsSourceConfigRegistry.create_config("cache_test_2", mock_repository)

    # 清除单个缓存
    NewsSourceConfigRegistry.clear_cache("cache_test_1")

    # 重新创建 cache_test_1
    config1_after = await NewsSourceConfigRegistry.create_config("cache_test_1", mock_repository)
    config2_after = await NewsSourceConfigRegistry.create_config("cache_test_2", mock_repository)

    # 验证 cache_test_1 是新实例，cache_test_2 是缓存实例
    assert config1_before is not config1_after  # 已清除，新实例
    assert config2_before is config2_after       # 未清除，缓存实例

    print(f"\n[OK] 单个缓存清除成功: cache_test_1 是新实例")
    print(f"[OK] 其他缓存保留: cache_test_2 仍是缓存实例")

    # 清除全部缓存
    NewsSourceConfigRegistry.clear_cache()

    # 重新创建所有配置
    config1_new = await NewsSourceConfigRegistry.create_config("cache_test_1", mock_repository)
    config2_new = await NewsSourceConfigRegistry.create_config("cache_test_2", mock_repository)

    # 验证都是新实例
    assert config1_after is not config1_new
    assert config2_after is not config2_new

    print(f"[OK] 全部缓存清除成功: 所有配置都是新实例")


def test_clear_registry():
    """测试清除注册表：验证注册表和缓存都被清空"""
    @NewsSourceConfigRegistry.register("registry_test")
    class RegistryConfig(MockNewsSourceConfig):
        pass

    # 验证注册成功
    assert NewsSourceConfigRegistry.has_config("registry_test")

    # 清空注册表
    NewsSourceConfigRegistry.clear_registry()

    # 验证注册表已清空
    assert not NewsSourceConfigRegistry.has_config("registry_test")
    assert len(NewsSourceConfigRegistry.list_registered()) == 0

    print(f"\n[OK] 注册表清除成功")
