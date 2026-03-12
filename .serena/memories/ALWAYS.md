# ⚠️ 必读规则（每次对话都适用）

## 🔴 最高优先级：修改源码前必须确认

**在修改任何源码文件之前，必须先：**
1. 描述要改哪个文件、改什么内容、为什么改
2. **等待用户确认后**，才能动手

只读操作（读文件、查看代码、分析逻辑）不受此限制。

---

## 架构红线（禁止事项）

- ❌ Domain 层禁止 import Infrastructure 层的任何模块
- ❌ 禁止绕过 Repository 接口直接操作数据库
- ❌ 禁止在 Crawler Node 层写业务逻辑（节点只负责流程）
- ❌ 禁止相对导入，必须用绝对导入
- ❌ 禁止泛化目录名（common / utils / misc）

---

## 代码规范（必须遵守）

### 命名
- 类名：PascalCase → `NewsLinkCrawlService`
- 函数/变量：snake_case → `build_request`
- 常量：UPPER_SNAKE_CASE
- 实体类必须以 `Entity` 结尾 → `CrawlResultEntity`
- 值对象以 `VO` 结尾，用 `Status` 不用 `State` → `NewsSourceStatusVO`
- DAO 方法参照 Java：`find_by_xxx` / `find_all_by_xxx` / `save` / `bulk_insert_ignore`
- 接口类前缀 `I` → `INewsCrawlRepository`

### 注释
- 统一使用**中文**
- 所有函数必须有 docstring
- 行内注释低密度（约 10-20 行一条）

### 其他
- 所有 I/O 操作使用 async/await
- 错误处理：Domain 层抛领域异常，Infrastructure 层转换为领域异常

---

## 项目当前状态（快速参考）

**触发方式**：ManualTrigger ✅ | APITrigger ⚠️（需 `pip install fastapi uvicorn`） | SchedulerTrigger ⚠️（需 `pip install apscheduler`）

**首次运行必须执行**：
```bash
mysql -u root -p < doc/sql/news_crawl.sql
```

**日常运行**：
```bash
python -m v1.DDD.app.src.main.main --source id_jawapos
```

**添加新闻源流程**：
1. 在 `app/src/resource/news_source/` 创建配置类
2. 继承 `AbstractNewsSourceConfig`，加 `@NewsSourceConfigRegistry.register("id")` 装饰器
3. 实现 `parse_response()` 和 `extract_category()`
4. 在 `__init__.py` 导入（触发注册）
5. 数据库插入对应 `news_source` 记录
