# data-nexus 当前系统架构

> 本文件是**当前系统的真实快照**，随代码变更同步更新（开发规范第 8 节）。
> 最近更新：2026-06-04　|　对应版本：**v0.01**（文档与治理基线，代码未开始）

---

## 1. 当前状态

| 阶段 | 状态 |
|---|---|
| 技术方案 | ✅ 已定稿（见 docs/技术方案.md v0.3） |
| 开发规范 | ✅ 已定稿（见 docs/开发规范.md v1.1） |
| 后端代码 | ⬜ 未开始 |
| 前端代码 | ⬜ 未开始 |

> 代码尚未开始，本文档先记录**规划架构**，开发推进后逐步替换为**实际架构**。

---

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Django + DRF |
| 调度 | APScheduler（单进程） |
| 元数据库 | SQLite |
| 业务数据源 | Oracle（python-oracledb thin） |
| Excel | openpyxl |
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia + Vite |
| 认证 | Django 内置用户 + DRF Token |

---

## 3. 模块（规划）

```
backend/
├── config/        # Django 配置、URL、APScheduler 初始化
├── core/          # oracle_client(只读执行) / excel(导出) / 加密
└── apps/
    ├── accounts/    # 用户、Token 认证
    ├── datasource/  # Oracle 数据源管理
    ├── query/       # SQL 查询任务、执行、预览
    └── execution/   # 执行记录、受控下载

frontend/
└── src/
    ├── views/       # datasource / task / execution / login
    ├── stores/      # Pinia
    └── api/         # axios 封装
```

---

## 4. 数据模型（规划，详见技术方案第 4 节）

- `DataSource`：Oracle 连接配置（密码加密）
- `QueryTask`：SQL 任务（含定时规则）
- `Execution`：执行记录（状态、行数、Excel 文件路径）
- `User`：内置用户

> 实际字段以迁移文件为准，落地后在此更新。

---

## 5. 接口清单（规划）

待后端实现后，在此登记实际生效的 REST 接口（路径、方法、用途、鉴权）。

---

## 6. 部署

- 生产：Linux（方式待定：systemd / Docker）
- 开发：本地 Windows，代码保持跨平台。

---

## 7. 变更记录指引

本文档每次架构/接口变更时更新；版本级变更说明见 `changelog/`。
