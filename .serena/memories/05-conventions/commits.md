# Git 提交规范

> Conventional Commits 风格的提交规范

## 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Type 类型

- `feat` - 新功能
- `fix` - Bug 修复
- `refactor` - 重构（不改变功能）
- `docs` - 文档变更
- `style` - 代码格式（不影响功能）
- `test` - 测试相关
- `chore` - 构建/工具/依赖变更
- `perf` - 性能优化

## Scope 范围

- `crawler` - 爬虫相关
- `config` - 配置相关
- `health-check` - 健康检查
- `infrastructure` - 基础设施
- `app` - 应用层
- `deps` - 依赖更新

## Subject 主题

- 使用中文
- 简洁明了（50字符内）
- 动词开头（添加、修复、重构）
- 不使用句号

## 示例

### 新功能
```
feat(crawler): 添加智能剪枝机制

实现连续空页和重复页剪枝功能：
- 连续 3 页为空自动停止
- 连续 3 页全部重复自动停止
- 可配置剪枝阈值
```

### Bug 修复
```
fix(config): 修复 NewsSourceMetadata 缺失 url 字段

- 添加 url 字段到 NewsSourceMetadata
- 更新 ORM Model 映射
- 修复相关测试用例
```

### 重构
```
refactor(crawler): 重构新闻链接爬虫服务模块结构

将原来的 service/crawl_layer/ 移动到 
service/single_news_link_crawl/crawl_layer/，
统一组织单源爬取相关服务
```

### 文档
```
docs(readme): 更新项目配置说明

添加 .env 配置示例和数据库初始化步骤
```

### 依赖更新
```
chore(deps): 更新依赖并配置测试环境

- 升级 SQLAlchemy 到 2.0
- 添加 pytest-asyncio
```

## 最佳实践

### 提交频率
- 完成一个独立功能点就提交
- 不要积累过多变更

### 提交粒度
- 一个提交只做一件事
- 避免混合多种类型的变更

### 提交前检查
- 运行测试确保通过
- 移除调试代码
- 检查代码风格

## 相关链接

- [任务清单](../06-tasks/pending) - 待完成任务
- [代码风格](code_style) - 代码规范
