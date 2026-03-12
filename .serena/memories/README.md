# 项目记忆系统

**最后更新**: 2026-03-11

## 记忆组织结构

```
01-architecture/       # 架构设计
  ├─ README            # 架构概览
  ├─ directory_structure  # 目录结构
  ├─ layers            # 分层架构
  ├─ patterns          # 设计模式
  └─ principles        # 设计原则

02-domain/             # 领域层
  ├─ config/           # 新闻源配置系统
  ├─ crawler/          # 爬虫核心逻辑
  └─ repository        # 仓储接口

03-infrastructure/     # 基础设施层
  ├─ database          # 数据库配置
  ├─ http              # HTTP客户端
  ├─ dao               # 数据访问对象
  └─ repository        # 仓储实现

04-application/        # 应用层（新增）
  ├─ README            # 应用层概览
  ├─ di_container      # 依赖注入容器
  ├─ lifecycle         # 生命周期管理
  ├─ services          # 应用服务
  ├─ trigger_system    # 触发器系统
  └─ config            # 应用配置

05-conventions/        # 编码规范
  ├─ code_style        # 代码风格
  ├─ naming            # 命名规范
  ├─ testing           # 测试规范
  └─ commits           # 提交规范

06-tasks/              # 任务管理
  ├─ checklist         # 检查清单
  └─ pending           # 待办事项

99-archive/            # 归档（已废弃功能）
  └─ health_check/     # 健康检查功能（已移除）
```

## 快速查找

### 我想了解...
- **项目整体架构** → `01-architecture/README`
- **DDD分层设计** → `01-architecture/layers`
- **目录结构** → `01-architecture/directory_structure`
- **新闻源配置** → `02-domain/config/README`
- **爬虫执行流程** → `02-domain/crawler/execution_flow`
- **应用启动流程** → `04-application/lifecycle`
- **触发器系统** → `04-application/trigger_system`
- **依赖注入** → `04-application/di_container`
- **数据库操作** → `03-infrastructure/database`
- **HTTP请求** → `03-infrastructure/http`

### 我想开发...
- **添加新闻源** → `02-domain/config/README` + `05-conventions/naming`
- **修改爬虫逻辑** → `02-domain/crawler/README`
- **添加新的触发方式** → `04-application/trigger_system`
- **修改数据库表** → `03-infrastructure/database` + `03-infrastructure/dao`

## 项目状态

**当前版本**: 研究阶段（试验性项目）
**主要功能**: 新闻链接爬取
**架构模式**: DDD + 清洁架构 + 触发器模式
**运行方式**: CLI命令行（手动触发）/ API触发（待启用）/ 定时任务（待启用）

## 重要提醒

⚠️ **首次运行必须执行数据库初始化**：
```bash
mysql -u root -p < doc/sql/news_crawl.sql
```

✅ **当前已实现的触发方式**：
- ManualTrigger（命令行手动触发）✅

⚠️ **框架已就绪但需安装依赖**：
- APITrigger（HTTP API触发）⚠️
- SchedulerTrigger（定时任务触发）⚠️

📋 **待实现**：
- MessageQueueTrigger（消息队列触发）❌