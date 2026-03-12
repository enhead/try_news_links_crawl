# 项目概览
> 这里三个文件显然是需要优化的，感觉很乱

**最后更新**: 2026-03-11

## 项目简介

这是一个研究性质的新闻链接爬取项目，用于探索快速修复新闻源的方法和可复用的爬取模式。

**项目性质**: 试验性项目（非最终版本）
**主要功能**: 爬取新闻链接
**架构风格**: DDD（领域驱动设计）+ 清洁架构 + 触发器模式

## 核心特性

### ✅ 已实现
1. **DDD分层架构**：触发层、应用层、领域层、基础设施层
2. **依赖注入容器**：使用 `dependency-injector` 管理依赖
3. **触发器模式**：支持多种触发方式（命令行、API、定时任务）
4. **新闻源配置系统**：注册表 + 工厂模式，易于扩展
5. **多层爬取系统**：顺序层 + 枚举层 + 映射层
6. **爬虫日志功能**：记录爬取过程和结果
7. **异步架构**：全异步实现（asyncio + httpx + SQLAlchemy）

### ⚠️ 框架已就绪（需安装依赖）
1. **API触发器**：HTTP REST API（需安装 FastAPI）
2. **定时任务触发器**：定时自动爬取（需安装 APScheduler）

### 📋 待实现
1. **消息队列触发器**：基于MQ的异步触发
2. **Web管理界面**：可视化管理和监控
3. **分布式爬虫**：支持多机集群

## 技术栈

**语言和框架**：
- Python 3.13
- dependency-injector（依赖注入）
- FastAPI（HTTP API，待启用）
- APScheduler（定时任务，待启用）

**数据库**：
- MySQL 8.x
- SQLAlchemy（异步ORM）
- asyncmy（MySQL异步驱动）

**HTTP客户端**：
- httpx（异步HTTP客户端）

**工具**：
- uv（依赖管理）
- pytest（测试）
- python-dotenv（环境变量）

## 架构概览
> TODO：这里感觉不太对，需要去看看DDD
> 
```
┌─────────────────────────────────────────────────────┐
│                  触发层 (Trigger)                   │
│  ManualTrigger ✅  APITrigger ⚠️  SchedulerTrigger ⚠️│
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │    应用层 (App)        │
         │  - DI容器              │
         │  - 配置管理            │
         │  - 生命周期管理        │
         │  - 应用服务（编排）    │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │   领域层 (Domain)      │
         │  - 新闻源配置系统      │
         │  - 爬虫核心逻辑        │
         │  - 多层爬取系统        │
         │  - 领域模型            │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │ 基础设施层 (Infra)     │
         │  - MySQL数据库         │
         │  - HTTP客户端          │
         │  - 持久化（DAO/Repo）  │
         └───────────────────────┘
```

## 数据库设计

**核心表**：
- `news_source`: 新闻源元数据
- `news_link`: 新闻链接
- `crawl_log`: 爬虫日志（新增）

**初始化**：
```bash
mysql -u root -p < doc/sql/news_crawl.sql
```

## 运行方式

### 前置条件

1. **数据库初始化**（首次运行必须）：
   ```bash
   mysql -u root -p < doc/sql/news_crawl.sql
   ```

2. **配置环境变量**：
   ```bash
   cp .env.example .env
   # 编辑 .env，配置数据库连接等
   ```

### 方式一：命令行运行（推荐入门）

```bash
# 爬取所有新闻源
python -m v1.DDD.app.src.main.main

# 爬取指定新闻源
python -m v1.DDD.app.src.main.main --source id_jawapos

# 爬取多个新闻源
python -m v1.DDD.app.src.main.main --source id_jawapos,sg_straits_times

# 列出所有可用新闻源
python -m v1.DDD.app.src.main.main --list-sources

# 调整日志级别
python -m v1.DDD.app.src.main.main --log-level DEBUG
```

### 方式二：Python脚本

```python
import asyncio
from v1.DDD.app.src.main.main import main_async

asyncio.run(main_async(
    source_ids=["id_jawapos"],  # 指定新闻源，None 表示所有
    list_only=False              # False 表示执行爬取
))
```

### 方式三：API触发（待启用）

**启用步骤**：
1. 安装依赖：`pip install fastapi uvicorn`
2. 取消注释 `trigger/api_trigger.py` 中的 TODO 代码
3. 启动：`python -m v1.DDD.trigger.api_trigger`
4. 访问：`http://localhost:8000/docs`

**API接口**：
```bash
# 爬取单个新闻源
curl -X POST http://localhost:8000/api/v1/crawl/single \
  -H "Content-Type: application/json" \
  -d '{"resource_id": "id_jawapos"}'

# 获取所有新闻源
curl http://localhost:8000/api/v1/sources
```

### 方式四：定时任务（待启用）

**启用步骤**：
1. 安装依赖：`pip install apscheduler`
2. 取消注释 `trigger/scheduler_trigger.py` 中的 TODO 代码
3. 配置 Cron 表达式
4. 启动：`python -m v1.DDD.trigger.scheduler_trigger`

## 添加新闻源

### 步骤

1. **创建配置类**：
   ```bash
   # 在 src/v1/DDD/app/src/resource/news_source/ 创建
   touch src/v1/DDD/app/src/resource/news_source/your_source_config.py
   ```

2. **实现配置类**：
   ```python
   from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import AbstractNewsSourceConfig
   from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.registry.news_source_config_registry import NewsSourceConfigRegistry
   
   @NewsSourceConfigRegistry.register("your_source_id")
   class YourSourceConfig(AbstractNewsSourceConfig):
       def parse_response(self, response, context):
           """解析响应，提取链接"""
           # 实现解析逻辑
           pass
       
       def extract_category(self, context):
           """提取分类信息"""
           # 实现分类提取逻辑
           pass
   ```

3. **在 `__init__.py` 中导入**：
   ```python
   # src/v1/DDD/app/src/resource/news_source/__init__.py
   from .your_source_config import YourSourceConfig
   ```

4. **在数据库中添加元数据**：
   ```sql
   INSERT INTO news_source (resource_id, name, domain, url, country, language, status)
   VALUES ('your_source_id', 'Your Source Name', 'example.com', 'https://example.com', 'XX', 'xx', 0);
   ```

5. **测试**：
   ```bash
   python -m v1.DDD.app.src.main.main --source your_source_id
   ```

## 目录结构（简化版）

```
src/v1/DDD/
├─ trigger/              # 触发层✨
│  ├─ base_trigger.py
│  ├─ api_trigger.py
│  └─ scheduler_trigger.py
│
├─ app/src/
│  ├─ main/              # 应用启动✨
│  │  ├─ main.py
│  │  ├─ application.py
│  │  ├─ DI/container.py
│  │  └─ config/app_config.py
│  └─ resource/
│     └─ news_source/    # 新闻源配置
│
├─ domain/               # 领域层
│  └─ http_news_links_crawl/
│     ├─ model/
│     ├─ service/
│     └─ repository/
│
└─ infrastructure/       # 基础设施层
   ├─ http/
   ├─ config/mysql/
   └─ persistent/
```

## 开发流程

### 1. 环境准备
```bash
# 克隆项目
git clone <repo>

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
vim .env

# 初始化数据库
mysql -u root -p < doc/sql/news_crawl.sql
```

### 2. 开发新功能
```bash
# 创建分支
git checkout -b feature/your-feature

# 开发...

# 运行测试
pytest app/test/

# 提交代码
git add .
git commit -m "feat: your feature"
git push origin feature/your-feature
```

### 3. 测试
```bash
# 单元测试
pytest app/test/

# 集成测试（爬取测试）
python -m v1.DDD.app.src.main.main --source id_jawapos --log-level DEBUG
```

## 常见问题

### Q1: 运行时提示 "未找到任何新闻源配置"

**原因**: 新闻源配置类未正确注册

**解决**:
1. 检查配置类是否使用了 `@NewsSourceConfigRegistry.register()` 装饰器
2. 检查 `__init__.py` 中是否导入了配置类
3. 检查 `.env` 中的 `NEWS_SOURCE_MODULES` 配置

### Q2: 运行时提示 "数据库连接失败"

**原因**: 数据库配置错误或数据库未启动

**解决**:
1. 检查 `.env` 文件中的数据库配置
2. 确保 MySQL 服务已启动
3. 确认数据库、表已创建：`mysql -u root -p < doc/sql/news_crawl.sql`

### Q3: 如何调试爬虫？

**方法**:
1. 使用 DEBUG 日志级别：
   ```bash
   python -m v1.DDD.app.src.main.main --log-level DEBUG
   ```
2. 爬取单个新闻源进行测试
3. 查看详细日志输出，定位问题

### Q4: 首次运行失败，提示表不存在

**原因**: 未执行数据库初始化脚本

**解决**:
```bash
mysql -u root -p < doc/sql/news_crawl.sql
```

## 项目规范

### 代码风格
- 遵循 PEP 8
- 使用类型提示
- 函数和类都需要 Docstring

### 命名规范
- 模块：小写 + 下划线（`news_link_crawl_service.py`）
- 类：大驼峰（`NewsLinkCrawlService`）
- 函数：小写 + 下划线（`crawl_single_source()`）
- 常量：大写 + 下划线（`DEFAULT_TIMEOUT`）

### 提交规范
```
feat: 新功能
fix: 修复bug
refactor: 重构
docs: 文档
test: 测试
chore: 构建/工具
```

## 扩展计划

### 短期（待实现）
- [ ] 启用 API 触发器
- [ ] 启用定时任务触发器
- [ ] 实现消息队列触发器
- [ ] 添加更多新闻源

### 中期
- [ ] Web管理界面
- [ ] 分布式爬虫支持
- [ ] 监控和告警系统
- [ ] 爬虫性能优化

### 长期
- [ ] 内容爬取（不仅是链接）
- [ ] 数据分析和可视化
- [ ] 多语言支持
- [ ] 云原生部署

## 相关文档

- **架构设计** → `01-architecture/README`
- **触发器系统** → `04-application/trigger_system`
- **新闻源配置** → `02-domain/config/README`
- **爬虫执行流程** → `02-domain/crawler/execution_flow`
- **数据库设计** → `03-infrastructure/database`

## 项目状态

**当前版本**: v1（研究阶段）
**代码质量**: 试验性（可能有不完善的地方）
**文档状态**: 持续更新中
**测试覆盖率**: 部分覆盖

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

（待添加）