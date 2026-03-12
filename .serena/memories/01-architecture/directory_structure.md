# 目录结构

**最后更新**: 2026-03-11

## 项目根目录

```
try_news_links_crawl/
├─ .env                         # 环境配置（不提交）
├─ .env.example                 # 环境配置示例
├─ .gitignore                   # Git忽略文件
├─ .python-version              # Python版本
├─ pyproject.toml               # 项目配置（uv）
├─ uv.lock                      # 依赖锁定文件
├─ README.md                    # 项目说明文档
├─ quick_start.py               # 快速启动脚本（待完善）
│
├─ doc/                         # 文档目录
│  └─ sql/
│     └─ news_crawl.sql         # 数据库初始化脚本（⚠️ 首次运行必须执行）
│
├─ src/v1/DDD/                  # 主代码目录（DDD架构）
│  │
│  ├─ trigger/                  # ✨ 触发层（新增）
│  │  ├─ __init__.py
│  │  ├─ base_trigger.py        # 触发器基类 + ManualTrigger
│  │  ├─ api_trigger.py         # API触发器（框架已就绪）
│  │  └─ scheduler_trigger.py   # 定时任务触发器（框架已就绪）
│  │
│  ├─ app/                      # 应用层
│  │  ├─ src/
│  │  │  ├─ main/               # ✨ 主应用（新增）
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ main.py          # CLI主程序
│  │  │  │  ├─ application.py   # 应用启动入口
│  │  │  │  ├─ DI/              # 依赖注入
│  │  │  │  │  ├─ __init__.py
│  │  │  │  │  └─ container.py  # DI容器
│  │  │  │  └─ config/          # 应用配置
│  │  │  │     ├─ __init__.py
│  │  │  │     └─ app_config.py # 配置对象
│  │  │  │
│  │  │  └─ resource/           # 资源配置
│  │  │     └─ news_source/     # 新闻源配置
│  │  │        ├─ __init__.py
│  │  │        └─ jawapos_config.py  # JawaPos配置
│  │  │
│  │  └─ test/                  # 测试
│  │     └─ http_news_links_crawl/
│  │        ├─ conftest.py
│  │        ├─ domain/service/impl/
│  │        │  └─ test_news_link_crawl_service.py
│  │        └─ infrastructure/repository/
│  │           └─ simple_test.py
│  │
│  ├─ domain/                   # 领域层
│  │  └─ http_news_links_crawl/
│  │     ├─ model/              # 领域模型
│  │     │  ├─ entity/          # 实体
│  │     │  │  ├─ crawl_context.py
│  │     │  │  ├─ crawl_result_entity.py
│  │     │  │  ├─ execution_phase_entity.py
│  │     │  │  ├─ layer_factor_entity.py
│  │     │  │  ├─ layer_node_result_entity.py
│  │     │  │  ├─ news_resource_crawl_factor_entity.py
│  │     │  │  ├─ news_source_metadata.py
│  │     │  │  └─ response_parse_result_entity.py
│  │     │  ├─ valobj/          # 值对象
│  │     │  │  ├─ news_source_status_vo.py
│  │     │  │  ├─ node_role_vo.py
│  │     │  │  ├─ node_status_vo.py
│  │     │  │  ├─ response_parse_result_status_vo.py
│  │     │  │  └─ stop_reason_vo.py
│  │     │  └─ aggregate/       # 聚合
│  │     │     └─ news_link_batch_aggregate.py
│  │     │
│  │     ├─ repository/         # 仓储接口
│  │     │  └─ base_news_links_crawl_repository.py
│  │     │
│  │     └─ service/            # 领域服务
│  │        ├─ base_news_crawl_application_service.py
│  │        ├─ impl/
│  │        │  └─ news_crawl_application_service.py  # 应用服务
│  │        ├─ config/          # 新闻源配置系统
│  │        │  └─ news_resource/
│  │        │     ├─ abstract_news_source_config.py
│  │        │     ├─ registry/
│  │        │     │  └─ news_source_config_registry.py
│  │        │     └─ factory/
│  │        │        └─ news_source_config_factory.py
│  │        └─ single_news_link_crawl/  # 爬虫核心
│  │           ├─ base_news_link_crawl_service.py
│  │           ├─ impl/
│  │           │  └─ news_link_crawl_service.py
│  │           └─ crawl_layer/  # 爬取层系统
│  │              ├─ abstract_layer.py
│  │              ├─ impl/
│  │              │  ├─ sequential_layer.py   # 顺序层
│  │              │  ├─ enumerable_layer.py   # 枚举层
│  │              │  └─ mapping_layer.py      # 映射层
│  │              ├─ crawl_node/
│  │              │  ├─ abstract_crawl_node.py
│  │              │  └─ impl/
│  │              │     └─ default_crawl_node.py
│  │              └─ factory/
│  │                 └─ layer_factory.py
│  │
│  └─ infrastructure/           # 基础设施层
│     ├─ config/
│     │  └─ mysql/              # MySQL配置
│     │     ├─ database.py
│     │     └─ settings.py
│     ├─ http/                  # HTTP客户端
│     │  ├─ httpx_adapter.py
│     │  ├─ request_parameter.py
│     │  └─ response.py
│     └─ persistent/            # 持久化
│        ├─ models/             # ORM模型
│        │  ├─ base.py
│        │  ├─ news_source.py
│        │  ├─ news_link.py
│        │  ├─ crawl_log.py     # ✨ 爬虫日志（新增）
│        │  └─ mapper/          # 模型映射器
│        │     ├─ news_source_mapper.py
│        │     ├─ news_link_mapper.py
│        │     └─ crawl_log_mapper.py
│        ├─ dao/                # 数据访问对象
│        │  ├─ news_source_dao.py
│        │  ├─ news_link_dao.py
│        │  └─ crawl_log_dao.py # ✨ 爬虫日志DAO（新增）
│        └─ repository/         # 仓储实现
│           └─ news_links_crawl_repository.py
│
├─ 新闻源检查结果/              # 检查结果（临时）
└─ 研究/                        # 研究资料（临时）
```

## 核心目录说明

### 触发层（trigger/）✨ 新增

**职责**：解耦触发方式和业务逻辑

**关键文件**：
- `base_trigger.py`: 触发器基类 + 手动触发器（已实现）
- `api_trigger.py`: API触发器（框架已就绪，需安装FastAPI）
- `scheduler_trigger.py`: 定时任务触发器（框架已就绪，需安装APScheduler）

**扩展点**：
- 添加新触发方式：继承 `BaseTrigger`，实现 `setup/start/stop`

### 应用层（app/src/main/）✨ 新增

**职责**：应用启动、依赖注入、服务编排

**关键文件**：
- `main.py`: CLI主程序，命令行参数解析
- `application.py`: 应用启动入口，生命周期管理
- `DI/container.py`: DI容器，管理所有依赖
- `config/app_config.py`: 应用配置对象

**启动流程**：
```
main() → create_app() → AppContainer → Application → Trigger → Service
```

### 资源配置（app/src/resource/news_source/）

**职责**：新闻源配置实现

**关键文件**：
- `jawapos_config.py`: JawaPos新闻源配置

**添加新闻源步骤**：
1. 在此目录创建配置类
2. 继承 `AbstractNewsSourceConfig`
3. 使用 `@NewsSourceConfigRegistry.register("resource_id")` 装饰器
4. 实现 `parse_response()` 和 `extract_category()` 方法
5. 在 `__init__.py` 中导入

### 领域层（domain/http_news_links_crawl/）

**职责**：核心业务逻辑

**关键子目录**：
- `model/`: 领域模型（实体、值对象、聚合）
- `repository/`: 仓储接口（依赖倒置）
- `service/`: 领域服务
  - `impl/news_crawl_application_service.py`: 应用服务（编排）
  - `single_news_link_crawl/`: 爬虫核心
  - `config/news_resource/`: 新闻源配置系统

**爬取层系统**：
```
crawl_layer/
├─ abstract_layer.py          # 层接口
├─ impl/
│  ├─ sequential_layer.py     # 顺序层（按顺序执行节点）
│  ├─ enumerable_layer.py     # 枚举层（并发执行多个节点）
│  └─ mapping_layer.py        # 映射层（键值对映射）
├─ crawl_node/                # 爬取节点
│  ├─ abstract_crawl_node.py
│  └─ impl/default_crawl_node.py
└─ factory/layer_factory.py   # 层工厂
```

### 基础设施层（infrastructure/）

**职责**：技术实现（HTTP、数据库、文件）

**关键子目录**：
- `config/mysql/`: MySQL数据库配置
- `http/`: HTTP客户端（httpx）
- `persistent/`: 持久化
  - `models/`: SQLAlchemy ORM模型
  - `dao/`: 数据访问对象
  - `repository/`: 仓储实现

**新增**：
- `models/crawl_log.py`: 爬虫日志ORM模型
- `dao/crawl_log_dao.py`: 爬虫日志DAO
- `mapper/crawl_log_mapper.py`: 爬虫日志映射器

### 测试（app/test/）

**结构**：
```
test/http_news_links_crawl/
├─ conftest.py                # 测试配置和fixture
├─ domain/service/impl/
│  └─ test_news_link_crawl_service.py
└─ infrastructure/repository/
   └─ simple_test.py
```

**运行测试**：
```bash
pytest app/test/
```

## 重要文件

### 配置文件

- **`.env`**: 环境配置（不提交，本地维护）
- **`.env.example`**: 配置示例（提交到Git）
- **`pyproject.toml`**: 项目依赖和配置（uv）

### 数据库

- **`doc/sql/news_crawl.sql`**: 数据库初始化脚本

  ⚠️ **首次运行必须执行**：
  ```bash
  mysql -u root -p < doc/sql/news_crawl.sql
  ```

### 启动入口

- **`src/v1/DDD/app/src/main/main.py`**: CLI主程序

  运行方式：
  ```bash
  # 爬取所有新闻源
  python -m v1.DDD.app.src.main.main
  
  # 爬取指定新闻源
  python -m v1.DDD.app.src.main.main --source id_jawapos
  
  # 列出所有新闻源
  python -m v1.DDD.app.src.main.main --list-sources
  ```

## 文件命名规范

### 通用规范

- **模块名**: 小写字母 + 下划线，如 `news_link_crawl_service.py`
- **类名**: 大驼峰，如 `NewsLinkCrawlService`
- **函数名**: 小写字母 + 下划线，如 `crawl_single_source()`
- **常量名**: 大写字母 + 下划线，如 `DEFAULT_TIMEOUT`

### 特定命名

**实体（Entity）**:
- 文件：`*_entity.py`
- 类：`*Entity`
- 示例：`crawl_result_entity.py` → `CrawlResultEntity`

**值对象（Value Object）**:
- 文件：`*_vo.py`
- 类：`*VO`
- 示例：`node_status_vo.py` → `NodeStatusVO`

**服务（Service）**:
- 文件：`*_service.py`
- 类：`*Service`
- 示例：`news_link_crawl_service.py` → `NewsLinkCrawlService`

**仓储（Repository）**:
- 文件：`*_repository.py`
- 接口类：`Base*Repository`
- 实现类：`*Repository`
- 示例：
  - 接口：`base_news_links_crawl_repository.py` → `BaseNewsLinksCrawlRepository`
  - 实现：`news_links_crawl_repository.py` → `NewsLinksCrawlRepository`

**DAO（Data Access Object）**:
- 文件：`*_dao.py`
- 类：`*DAO`
- 示例：`news_link_dao.py` → `NewsLinkDAO`

**配置（Config）**:
- 文件：`*_config.py`
- 类：`*Config`
- 示例：`app_config.py` → `AppConfig`

**触发器（Trigger）**:
- 文件：`*_trigger.py`
- 类：`*Trigger`
- 示例：`api_trigger.py` → `APITrigger`

## 模块导入路径

### 绝对导入（推荐）

```python
# 领域层
from v1.DDD.domain.http_news_links_crawl.service.impl.news_crawl_application_service import NewsCrawlApplicationService
from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_result_entity import CrawlResultEntity

# 基础设施层
from v1.DDD.infrastructure.http.httpx_adapter import HttpAdapter
from v1.DDD.infrastructure.persistent.repository.news_links_crawl_repository import NewsLinksCrawlRepository

# 应用层
from v1.DDD.app.src.main.DI.container import AppContainer
from v1.DDD.app.src.main.config.app_config import AppConfig
from v1.DDD.app.src.main.application import create_app

# 触发层
from v1.DDD.trigger.base_trigger import BaseTrigger, ManualTrigger
```

### 相对导入（限定范围内使用）

```python
# 在同一模块内
from .abstract_layer import AbstractLayer
from ..crawl_node.impl.default_crawl_node import DefaultCrawlNode
```

## Git忽略规则

**.gitignore** 重点：
```gitignore
# 环境配置
.env

# Python缓存
__pycache__/
*.pyc
*.pyo

# 虚拟环境
.venv/
venv/

# IDE
.idea/
.vscode/

# 日志和临时文件
*.log
*.tmp

# 测试结果
.pytest_cache/
test-output/
```

## 新增文件清单（vs 旧版本）

### 触发层✨
```
+ trigger/base_trigger.py
+ trigger/api_trigger.py
+ trigger/scheduler_trigger.py
```

### 应用层✨
```
+ app/src/main/main.py
+ app/src/main/application.py
+ app/src/main/DI/container.py
+ app/src/main/config/app_config.py
```

### 领域层更新
```
~ domain/.../service/impl/news_crawl_application_service.py  # 重构
~ domain/.../model/entity/crawl_context.py                   # 更新
+ domain/.../model/entity/execution_phase_entity.py          # 新增
```

### 基础设施层更新
```
+ infrastructure/persistent/models/crawl_log.py
+ infrastructure/persistent/dao/crawl_log_dao.py
+ infrastructure/persistent/models/mapper/crawl_log_mapper.py
~ infrastructure/persistent/repository/news_links_crawl_repository.py  # 更新
```

### 归档（已移除）🗑️
```
- domain/.../service/health_check/  # 健康检查功能已移除
```

## 相关记忆

- **架构概览** → `01-architecture/README`
- **分层架构** → `01-architecture/layers`
- **应用层概览** → `04-application/README`
- **触发器系统** → `04-application/trigger_system`
- **DI容器** → `04-application/di_container`