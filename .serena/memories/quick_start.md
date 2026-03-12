# 快速开始指南

**最后更新**: 2026-03-11

## ⚠️ 首次运行必读

### 1. 数据库初始化（必须执行）

**运行项目前必须先执行数据库初始化脚本：**

```bash
# 在项目根目录执行
mysql -u root -p < doc/sql/news_crawl.sql
```

这个脚本会自动：
- ✅ 创建数据库 `news_crawl`
- ✅ 创建 3 张核心表：`news_source`、`news_link`、`crawl_log`
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

**API 接口**：
```
POST /api/v1/crawl/single        - 爬取单个新闻源
POST /api/v1/crawl/batch         - 批量爬取
POST /api/v1/crawl/all           - 爬取所有
GET  /api/v1/sources             - 获取新闻源列表
GET  /api/v1/health              - 健康检查
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

**Cron 表达式示例**：
```python
"0 2 * * *"     # 每天凌晨2点
"0 */2 * * *"   # 每2小时
"0 0 * * 1"     # 每周一凌晨
"0 0 1 * *"     # 每月1号凌晨
```

---

## 📚 常用命令

### 数据库操作

```bash
# 初始化数据库
mysql -u root -p < doc/sql/news_crawl.sql

# 查看新闻源列表
mysql -u root -p -e "USE news_crawl; SELECT * FROM news_source;"

# 查看爬取的链接数量
mysql -u root -p -e "USE news_crawl; SELECT COUNT(*) FROM news_link;"

# 查看爬取日志
mysql -u root -p -e "USE news_crawl; SELECT * FROM crawl_log ORDER BY created_at DESC LIMIT 10;"
```

### 爬虫运行

```bash
# 基本运行
python -m v1.DDD.app.src.main.main

# 指定新闻源
python -m v1.DDD.app.src.main.main --source id_jawapos

# 调试模式
python -m v1.DDD.app.src.main.main --source id_jawapos --log-level DEBUG

# 列出所有新闻源
python -m v1.DDD.app.src.main.main --list-sources
```

### 测试

```bash
# 运行所有测试
pytest app/test/

# 运行特定测试
pytest app/test/http_news_links_crawl/domain/service/impl/test_news_link_crawl_service.py

# 详细输出
pytest app/test/ -v

# 显示打印输出
pytest app/test/ -s
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
2. 确保 MySQL 服务已启动：`sudo systemctl start mysql`
3. 确认数据库、表已创建：`mysql -u root -p < doc/sql/news_crawl.sql`

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

### Q5: 首次运行失败，提示表不存在

**原因**: 未执行数据库初始化脚本

**解决**:
```bash
mysql -u root -p < doc/sql/news_crawl.sql
```

---

## 🏗️ 生产环境部署建议

### 方案 A: API + 定时任务组合（推荐）

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

### 方案 B: 纯定时任务

适合只需要定时自动爬取的场景：

```bash
python -m v1.DDD.trigger.scheduler_trigger
```

配合 systemd/supervisor 守护进程管理。

### 方案 C: 纯 API 服务

适合需要外部系统触发的场景：

```bash
python -m v1.DDD.trigger.api_trigger
```

---

## 📧 下一步

- **了解架构** → 查看 `01-architecture/README` 记忆
- **添加新闻源** → 查看 `02-domain/config/README` 记忆
- **了解爬虫流程** → 查看 `02-domain/crawler/execution_flow` 记忆
- **扩展触发方式** → 查看 `04-application/trigger_system` 记忆

---

**祝你使用愉快！** 🎉