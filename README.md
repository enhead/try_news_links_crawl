# 研究尝试新闻源

- 修新闻源，尝试下，能否找到快速修的方法，找找有无可复用的方法
- 尝试研究项目，并不是最终的项目

---

# 新闻爬虫运行指南

## ⚠️ 首次运行必读

### 1. 数据库初始化（必须）

**运行项目前必须先执行数据库初始化脚本：**

```bash
# 在项目根目录执行
mysql -u root -p < doc/sql/news_crawl.sql
```

这个脚本会自动：
- ✅ 创建数据库 `news_crawl`
- ✅ 创建 3 张核心表：`news_source`、`news_link`、`news_content`
- ✅ 插入初始新闻源数据（`id_jawapos`）
- ✅ 验证并显示结果

**验证数据库初始化成功：**

```bash
mysql -u root -p -e "USE news_crawl; SELECT * FROM news_source;"
```

应该看到：
```
+----+-------------+-----------+------------------+------------------------+---------+----------+--------+
| id | resource_id | name      | domain           | url                    | country | language | status |
+----+-------------+-----------+------------------+------------------------+---------+----------+--------+
|  1 | id_jawapos  | Jawa Pos  | www.jawapos.com  | https://www.jawapos.com| ID      | id       |      0 |
+----+-------------+-----------+------------------+------------------------+---------+----------+--------+
```

### 2. 配置文件

确保项目根目录下有 `.env` 文件：

```bash
# 复制示例配置（如果还没有）
cp .env.example .env

# 编辑配置
vim .env
```

关键配置项：

```ini
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=news_crawl

# 新闻源模块配置
NEWS_SOURCE_MODULES=v1.DDD.app.src.resource.news_source
```

---

## 🚀 快速开始

### 环境准备

```bash
# 安装基础依赖
pip install -r requirements.txt

# 可选：安装 API 触发器依赖
pip install fastapi uvicorn

# 可选：安装定时任务触发器依赖
pip install apscheduler
```

---

## 🎯 运行方式

### 方式一：命令行直接运行（推荐入门）

#### 1. 爬取所有新闻源

```bash
python -m v1.DDD.app.src.main.main
```

#### 2. 爬取指定新闻源

```bash
python -m v1.DDD.app.src.main.main --source id_jawapos
```

#### 3. 爬取多个新闻源

```bash
python -m v1.DDD.app.src.main.main --source id_jawapos,sg_straits_times
```

#### 4. 列出所有可用新闻源

```bash
python -m v1.DDD.app.src.main.main --list-sources
```

#### 5. 调整日志级别

```bash
python -m v1.DDD.app.src.main.main --log-level DEBUG
```

### 方式二：使用 Python 脚本

创建一个运行脚本：

```python
# run_crawler.py
import asyncio
from v1.DDD.app.src.main.main import main_async

asyncio.run(main_async(
    source_ids=["id_jawapos"],  # 指定新闻源，None 表示所有
    list_only=False              # False 表示执行爬取
))
```

运行：

```bash
python run_crawler.py
```

---

## 🏗️ 触发器架构

### 架构概览

```
触发层 (Trigger Layer)
  ├─ ManualTrigger       - 手动触发（命令行）
  ├─ APITrigger          - HTTP API 触发
  ├─ SchedulerTrigger    - 定时任务触发
  └─ MessageQueueTrigger - 消息队列触发 (TODO)

应用层 (Application Layer)
  └─ NewsCrawlApplicationService

领域层 (Domain Layer)
  └─ NewsLinkCrawlService

基础设施层 (Infrastructure Layer)
  ├─ HttpAdapter
  ├─ NewsLinksCrawlRepository
  └─ Database
```

### 当前实现

#### ✅ ManualTrigger (已实现)

- **用途**: 命令行直接触发
- **文件**: `src/v1/DDD/app/src/main/main.py`
- **适用场景**:
  - 开发调试
  - 一次性运行
  - CI/CD 脚本

#### ⚠️ APITrigger (框架已就绪，需安装依赖)

- **用途**: 通过 HTTP REST API 触发
- **文件**: `src/v1/DDD/trigger/api_trigger.py`
- **启用步骤**:
  1. 安装依赖: `pip install fastapi uvicorn`
  2. 取消注释代码中的 TODO 部分
  3. 运行: `python -m v1.DDD.trigger.api_trigger`

- **API 接口**:
  ```
  POST /api/v1/crawl/single        - 爬取单个新闻源
  POST /api/v1/crawl/batch         - 批量爬取
  POST /api/v1/crawl/all           - 爬取所有
  GET  /api/v1/sources             - 获取新闻源列表
  GET  /api/v1/health              - 健康检查
  ```

#### ⚠️ SchedulerTrigger (框架已就绪，需安装依赖)

- **用途**: 定时自动触发
- **文件**: `src/v1/DDD/trigger/scheduler_trigger.py`
- **启用步骤**:
  1. 安装依赖: `pip install apscheduler`
  2. 取消注释代码中的 TODO 部分
  3. 运行: `python -m v1.DDD.trigger.scheduler_trigger`

- **Cron 表达式示例**:
  ```python
  "0 2 * * *"     # 每天凌晨2点
  "0 */2 * * *"   # 每2小时
  "0 0 * * 1"     # 每周一凌晨
  "0 0 1 * *"     # 每月1号凌晨
  ```

---

## 🔧 后续扩展

### 1. 启用 API 触发器

**步骤**：

1. 安装依赖：
   ```bash
   pip install fastapi uvicorn pydantic
   ```

2. 编辑 `src/v1/DDD/trigger/api_trigger.py`：
   - 取消注释所有 `# TODO: 取消注释以启用` 的代码块

3. 启动服务：
   ```bash
   python -m v1.DDD.trigger.api_trigger
   ```

4. 访问 API 文档：
   ```
   http://localhost:8000/docs
   ```

5. 调用 API：
   ```bash
   # 爬取单个新闻源
   curl -X POST http://localhost:8000/api/v1/crawl/single \
     -H "Content-Type: application/json" \
     -d '{"resource_id": "id_jawapos"}'

   # 获取所有新闻源
   curl http://localhost:8000/api/v1/sources
   ```

### 2. 启用定时任务触发器

**步骤**：

1. 安装依赖：
   ```bash
   pip install apscheduler
   ```

2. 编辑 `src/v1/DDD/trigger/scheduler_trigger.py`：
   - 取消注释所有 `# TODO: 取消注释以启用` 的代码块

3. 配置任务（可选）：
   ```python
   # 在 _add_default_jobs() 方法中配置
   self.add_job(
       job_id="crawl_all_daily",
       cron="0 2 * * *",     # 每天凌晨2点
       source_ids=None,      # 爬取所有新闻源
       description="每日全量爬取"
   )
   ```

4. 启动服务：
   ```bash
   python -m v1.DDD.trigger.scheduler_trigger
   ```

### 3. 实现消息队列触发器

**框架已预留**，实现步骤：

1. 选择 MQ 技术（RabbitMQ / Kafka / Redis Streams）

2. 编辑 `src/v1/DDD/trigger/base_trigger.py` 中的 `MessageQueueTrigger`

3. 实现核心方法：
   - `setup()`: 连接 MQ
   - `start()`: 消费消息
   - `stop()`: 关闭连接

4. 消息格式示例：
   ```json
   {
     "task_type": "crawl_single",
     "resource_id": "id_jawapos",
     "timestamp": "2024-01-01T00:00:00Z"
   }
   ```

### 4. 生产环境部署建议

#### 方案 A: API + 定时任务组合（推荐）

```
┌─────────────────┐
│  APScheduler    │  定时任务（后台自动）
│  每天凌晨2点    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  FastAPI        │  HTTP API（手动触发）
│  监听 8000 端口 │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  爬虫服务        │
│  应用层 + 领域层 │
└─────────────────┘
```

启动脚本：

```python
# production.py
import asyncio
from v1.DDD.app.src.main.application import create_app
from v1.DDD.trigger.api_trigger import FastAPITrigger
from v1.DDD.trigger.scheduler_trigger import SchedulerTrigger

async def main():
    app = await create_app()

    # 启动 API 触发器（后台）
    api_trigger = FastAPITrigger(app.container, port=8000)
    asyncio.create_task(api_trigger.run())

    # 启动定时任务触发器（阻塞）
    scheduler = SchedulerTrigger(app.container)
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 方案 B: 纯定时任务

适合只需要定时自动爬取的场景：

```bash
python -m v1.DDD.trigger.scheduler_trigger
```

配合 systemd/supervisor 守护进程管理。

#### 方案 C: 纯 API 服务

适合需要外部系统触发的场景：

```bash
python -m v1.DDD.trigger.api_trigger
```

---

## ❓ 常见问题

### Q1: 运行时提示 "未找到任何新闻源配置"

**原因**: 新闻源配置类未正确注册

**解决**:
1. 检查 `src/v1/DDD/app/src/resource/news_source/` 目录下是否有配置类
2. 确保 `__init__.py` 中导入了配置类
3. 确保配置类使用了 `@NewsSourceConfigRegistry.register()` 装饰器

### Q2: 运行时提示 "数据库连接失败"

**原因**: 数据库配置错误或数据库未启动

**解决**:
1. 检查 `.env` 文件中的数据库配置
2. 确保 MySQL 服务已启动
3. 确认数据库、表已创建

### Q3: 如何添加新的新闻源？

**步骤**:
1. 在 `src/v1/DDD/app/src/resource/news_source/` 创建配置类
2. 继承 `AbstractNewsSourceConfig`
3. 使用 `@NewsSourceConfigRegistry.register("resource_id")` 装饰器
4. 实现 `parse_response()` 和 `extract_category()` 方法
5. 在 `__init__.py` 中导入
6. 在数据库中添加对应的元数据记录

### Q4: 如何调试爬虫？

**方法**:
1. 使用 DEBUG 日志级别：
   ```bash
   python -m v1.DDD.app.src.main.main --log-level DEBUG
   ```

2. 爬取单个新闻源进行测试：
   ```bash
   python -m v1.DDD.app.src.main.main --source id_jawapos
   ```

3. 查看详细日志输出，定位问题

### Q5: 如何在 Docker 中运行？

**步骤**:
1. 创建 Dockerfile：
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   CMD ["python", "-m", "v1.DDD.app.src.main.main"]
   ```

2. 构建镜像：
   ```bash
   docker build -t news-crawler .
   ```

3. 运行容器：
   ```bash
   docker run --env-file .env news-crawler
   ```

---

## 📚 相关文档

- [架构设计](./docs/architecture.md)
- [新闻源配置指南](./docs/news_source_config.md)
- [API 接口文档](./docs/api.md)
- [数据库设计](./docs/database.md)

---

## 📧 联系方式

如有问题或建议，请联系开发团队。
