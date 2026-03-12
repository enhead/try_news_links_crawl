# 测试规范

> 单元测试、集成测试、测试命名规范

## 测试目录结构

```
src/v1/DDD/app/test/
└── http_news_links_crawl/
    ├── domain/
    │   └── service/
    │       └── impl/
    │           └── test_news_link_crawl_service.py
    └── infrastructure/
        └── repository/
            └── test_news_links_crawl_repository.py
```

## 测试文件命名

- **前缀**：`test_`
- **对应源文件**：`test_{source_file_name}.py`

## 测试函数命名

- **前缀**：`test_`
- **语义化**：`test_{what}_{scenario}`
- **示例**：`test_execute_crawl_success`

## 文件头部注释

```python
\"\"\"
NewsLinkCrawlService 集成测试

测试目标: 完整测试 execute_crawl 方法
测试站点: https://www.example.com

运行命令:
  # 运行所有测试
  pytest test/xxx/test_xxx.py
  
  # 运行单个测试
  pytest test/xxx/test_xxx.py::test_xxx - 测试 XXX 功能

验证内容:
1. 能成功构建 layer 树
2. 能发送 HTTP 请求并解析
3. 分页机制正常工作
\"\"\"
```

## 测试类型

### 单元测试
- 测试单个类/函数
- Mock 外部依赖
- 快速执行

### 集成测试
- 测试多个模块协作
- 使用真实依赖（数据库、HTTP）
- 较慢执行

### 端到端测试
- 测试完整业务流程
- 使用真实环境
- 最慢执行

## Pytest 使用

### 基本命令
```bash
# 运行所有测试
pytest src/v1/DDD/app/test/

# 运行特定文件
pytest test/xxx/test_xxx.py

# 运行特定测试
pytest test/xxx/test_xxx.py::test_xxx

# 显示详细输出
pytest test/xxx/test_xxx.py -v -s

# 显示日志
pytest test/xxx/test_xxx.py --log-cli-level=DEBUG
```

### Fixture 使用

```python
@pytest.fixture
def mock_repository():
    repo = MockRepository()
    return repo

@pytest.fixture(autouse=True)
def clean_registry():
    \"\"\"每个测试前后清空注册表\"\"\"
    NewsSourceConfigRegistry.clear_registry()
    yield
    NewsSourceConfigRegistry.clear_registry()
```

### 异步测试

```python
@pytest.mark.asyncio
async def test_execute_crawl():
    service = NewsLinkCrawlService()
    result = await service.execute_crawl(crawl_factor)
    assert result.total_new > 0
```

## 断言规范

```python
# ✅ 推荐：明确的断言
assert result.total_new > 0
assert len(result.errors) == 0
assert config.source_id == "sg_straits_times"

# ❌ 避免：模糊的断言
assert result
assert config
```

## Mock 使用

```python
from unittest.mock import AsyncMock, MagicMock

# Mock 异步方法
mock_repo = AsyncMock()
mock_repo.get_source_by_resource_id.return_value = metadata

# Mock 同步方法
mock_config = MagicMock()
mock_config.source_id = "test_source"
```

## 测试覆盖

### 核心业务逻辑
- Domain 层必须有单元测试
- 覆盖率 > 80%

### 集成测试
- Infrastructure 层需要集成测试
- Repository、DAO 层测试

### 端到端测试
- Application 层需要端到端测试
- 测试完整流程

## 测试隔离

- 每个测试独立运行
- 清理测试数据（使用 fixture）
- 不依赖测试顺序

## 相关链接

- [快速开始](../../quick_start) - 运行测试命令
- [代码风格](code_style) - 测试文件头部注释
