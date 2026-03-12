# 🔧 基础设施层概览

> 技术实现细节：数据库、HTTP、Repository

## 核心组件

- **数据库设计** - MySQL 表结构
- **HTTP 适配器** - httpx 封装
- **Repository 实现** - 仓储模式实现
- **DAO 层** - 数据访问对象

## 📁 本目录文件

- **[database](database)** - 数据库设计和表结构
- **[http](http)** - HTTP 客户端封装
- **[repository](repository)** - INewsCrawlRepository 实现
- **[dao](dao)** - DAO 层设计

## 实现原则

### 依赖倒置
- Infrastructure 层实现 Domain 层定义的接口
- 不在 Domain 层引入技术细节

### 职责分离
- **DAO** - 纯数据库操作
- **Repository** - 业务语义的数据访问
- **Mapper** - ORM Model ↔ 领域对象转换

## 相关链接

- [领域层](../02-domain/README) - 接口定义
- [应用层](../04-application/README) - 使用基础设施
