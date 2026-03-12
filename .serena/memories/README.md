# 项目记忆系统

**最后更新**: 2026-03-11

## ⚠️ 首先阅读

**`ALWAYS.md`** - 每次对话都必须遵守的规则（修改源码前需确认、架构红线、代码规范）

---

## 记忆组织结构

```
ALWAYS.md              # ⚠️ 必读：每次对话都适用的规则
overview.md            # 项目关键事实速查
quick_start.md         # 常用命令和前置条件

01-architecture/       # 架构设计
  ├─ README            # 架构概览（含架构图）
  ├─ directory_structure  # 完整目录结构
  ├─ layers            # 分层架构说明
  ├─ patterns          # 设计模式总览
  └─ principles        # DDD & SOLID 原则

02-domain/             # 领域层
  ├─ config/           # 新闻源配置系统
  ├─ crawler/          # 爬虫核心逻辑
  └─ repository        # 仓储接口设计

03-infrastructure/     # 基础设施层
  ├─ database          # 数据库表结构
  ├─ http              # HTTP 多适配器架构
  ├─ dao               # DAO 层设计
  ├─ repository        # Repository 实现
  └─ transaction       # 事务管理

04-application/        # 应用层
  ├─ README            # 应用层概览
  ├─ di_container      # 依赖注入容器
  ├─ lifecycle         # 生命周期管理
  ├─ trigger_system    # 触发器系统
  ├─ services          # 应用服务
  └─ config            # 应用配置

05-conventions/        # 编码规范
  ├─ code_style        # 代码风格（注释、异步、错误处理）
  ├─ naming            # 命名规范（详细版）
  ├─ testing           # 测试规范
  └─ commits           # Git 提交规范

06-tasks/              # 任务管理
  ├─ pending           # 待办事项（含上下文和卡点）
  └─ checklist         # 提交前检查清单
```

---

## 快速查找

### 我想了解…
- **整体架构** → `01-architecture/README`
- **爬虫执行流程** → `02-domain/crawler/execution_flow`
- **触发器系统** → `04-application/trigger_system`
- **HTTP 反爬方案** → `03-infrastructure/http`

### 我想开发…
- **添加新闻源** → `02-domain/config/README`
- **修改爬虫层逻辑** → `02-domain/crawler/layers`
- **添加触发方式** → `04-application/trigger_system`
- **修改数据库** → `03-infrastructure/database` + `03-infrastructure/dao`
