# 项目概览

**最后更新**: 2026-03-11

**项目性质**：研究性质的新闻链接爬取项目（试验性，非最终版本）

**技术栈**：Python 3.13 | MySQL 8.x + SQLAlchemy(async) | httpx / curl_cffi | dependency-injector

---

## 架构

DDD + 清洁架构，4层结构：

```
触发层 (Trigger) → 应用层 (App) → 领域层 (Domain) ← 基础设施层 (Infra)
```

**依赖方向**：单向向内，Domain 层不依赖任何外层，Infrastructure 层实现 Domain 层定义的接口。

---

## 已完成功能

- DDD 分层架构（4层）
- 依赖注入容器（dependency-injector）
- ManualTrigger（命令行触发）✅
- 新闻源配置系统（注册表 + 工厂模式）
- 多层爬取系统（顺序层 + 枚举层 + 映射层）
- 智能剪枝（连续空页 / 重复页自动停止）
- 多适配器 HTTP（httpx + curl_cffi，支持反爬）
- 爬虫日志（crawl_log 表）

---

## 数据库表

| 表名 | 用途 |
|------|------|
| `news_source` | 新闻源元数据（resource_id, name, domain, url, country, language, status） |
| `news_link` | 爬取的链接（url唯一, category, crawl_params, is_parse, is_translated） |
| `crawl_log` | 爬虫执行日志 |

---

## 已有新闻源

| resource_id | 名称 | 国家 |
|-------------|------|------|
| `id_jawapos` | Jawa Pos | 印尼 |

---

## 关键路径速查

| 我要做的事 | 去哪里看 |
|-----------|---------|
| 了解架构 | `01-architecture/README` |
| 添加新闻源 | `02-domain/config/README` |
| 修改爬虫逻辑 | `02-domain/crawler/README` |
| 理解执行流程 | `02-domain/crawler/execution_flow` |
| 添加触发方式 | `04-application/trigger_system` |
| 修改数据库 | `03-infrastructure/database` + `03-infrastructure/dao` |
