# data-nexus 当前系统架构

> 本文件是**当前系统的真实快照**，随代码变更同步更新（开发规范第 8 节）。
> 最近更新：2026-06-04　|　对应版本：**v0.02**（后端骨架 + 安全核心，已跑通验证）

---

## 1. 当前状态

| 阶段 | 状态 |
|---|---|
| 技术方案 | ✅ 已定稿（见 docs/技术方案.md v0.3） |
| 开发规范 | ✅ 已定稿（见 docs/开发规范.md v1.1） |
| 后端代码 | 🟡 骨架 + 安全核心已完成（v0.02，已跑通：check/migrate/测试/lint） |
| 前端代码 | ⬜ 未开始（计划 v0.03） |

> 业务 app（datasource/query/execution）尚未实现，规划见第 3 节。

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

## 3. 模块

图例：✅ 已实现　⬜ 规划中

```
backend/                        ✅ v0.02
├── config/                     ✅ Django 配置、URL、健康检查
│   ├── settings.py             ✅ .env 注入、DRF Token、CORS、安全护栏参数
│   └── urls.py                 ✅ /api/health/
├── core/                       ✅ 安全核心（含单元测试）
│   ├── sql_guard.py            ✅ 只读 SQL 校验（第二道防线）
│   ├── oracle_client.py        ✅ 绑定变量 + 流式 fetch + 行数上限 + 超时
│   ├── excel.py                ✅ openpyxl 流式导出
│   └── crypto.py               ✅ Fernet 加解密（数据源密码）
├── tests/                      ✅ test_sql_guard / test_excel（24 用例）
└── apps/                       ⬜ 业务应用
    ├── accounts/               ⬜ 用户、Token 认证
    ├── datasource/             ⬜ Oracle 数据源管理
    ├── query/                  ⬜ SQL 查询任务、执行、预览
    └── execution/              ⬜ 执行记录、受控下载

frontend/                       ⬜ v0.03（Vue3 + Element Plus）
```

> APScheduler 定时调度在业务 app 落地后接入（见技术方案 6.2 / 8.1）。

---

## 4. 数据模型（规划，详见技术方案第 4 节）

- `DataSource`：Oracle 连接配置（密码加密）
- `QueryTask`：SQL 任务（含定时规则）
- `Execution`：执行记录（状态、行数、Excel 文件路径）
- `User`：内置用户

> 实际字段以迁移文件为准，落地后在此更新。

---

## 5. 接口清单

| 路径 | 方法 | 用途 | 鉴权 | 状态 |
|---|---|---|---|---|
| `/api/health/` | GET | 健康检查 | 无 | ✅ |
| `/admin/` | - | Django 后台 | 登录 | ✅ |

> 业务接口（数据源/任务/执行/下载）随 app 实现登记。

## 5.1 本地启动（开发，Windows）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env   # 然后填写 SECRET_KEY / FERNET_KEY
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
# 质量检查：python -m ruff check . / python -m black . / python -m pytest
```

---

## 6. 部署

- 生产：Linux（方式待定：systemd / Docker）
- 开发：本地 Windows，代码保持跨平台。

---

## 7. 变更记录指引

本文档每次架构/接口变更时更新；版本级变更说明见 `changelog/`。
