# 🎯 爬虫领域概览

> 多层级爬取系统的核心实现

## 核心概念

### 三层嵌套结构
爬虫采用多层嵌套结构，每层负责一个维度的参数遍历：
- **EnumerableLayer（枚举层）** - 遍历固定值列表
- **MappingLayer（映射层）** - 根据依赖关系动态生成参数
- **SequentialLayer（顺序层）** - 叶子层，负责翻页爬取

### 执行流程
```
Layer 树构建 → 递归执行 → Node 爬取 → 智能剪枝
```

## 📖 阅读路径

### 理解爬虫机制
```
1. layers → 三种层类型详解
2. nodes → 爬取节点实现
3. execution_flow → 完整执行流程
4. pruning → 智能剪枝机制
5. services → 领域服务
```

## 📁 本目录文件

- **[layers](layers)** - 三种层类型（枚举/映射/顺序）
- **[nodes](nodes)** - 爬取节点（DefaultCrawlNode）
- **[execution_flow](execution_flow)** - Layer 树构建和执行流程
- **[pruning](pruning)** - 智能剪枝机制
- **[services](services)** - 领域服务（INewsLinkCrawlService）

## 架构特点

### 职责分离
- **Layer**：参数遍历和层级管理
- **Node**：单次请求、解析、去重、保存
- **Config**：请求构建和响应解析（见 [config](../config/README)）

### 组合模式
层可以嵌套形成树状结构，支持复杂的多维度遍历

### 工厂模式
使用 CrawlLayerFactory 装饰器注册和创建层实例

## 相关链接

- [配置管理](../config/README) - 新闻源配置体系
- [架构设计](../../01-architecture/patterns) - 设计模式总览
