# data-nexus 当前系统架构

> 本文件是**当前系统的真实快照**，随代码变更同步更新（开发规范第 8 节）。
> 最近更新：2026-06-05　|　对应版本：**v0.07**（前端双布局重构 + 角色分流，dev 分支）

---

## 1. 当前状态

| 阶段 | 状态 |
|---|---|
| 技术方案 | ✅ 已定稿（见 docs/技术方案.md v0.4） |
| 开发规范 | ✅ 已定稿（见 docs/开发规范.md v1.1） |
| 后端代码 | 🟡 安全核心 + 认证 + 数据模型/权限判定（v0.06，35 测试通过） |
| 前端代码 | 🟡 **双布局（用户端/管理端）+ 角色分流**（v0.07，build/lint 通过） |

> 当前在 `dev` 分支进行「重构基线」大改版（v0.06 起）。后端模型已落地，API 与前端重构随后续版本推进。

---

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Django + DRF |
| 调度 | APScheduler（单进程，后续接入） |
| 元数据库 | SQLite |
| 业务数据源 | Oracle（python-oracledb thin） |
| Excel | openpyxl |
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia + Vite |
| 认证 | 自定义 User + DRF Token |

---

## 3. 模块

图例：✅ 已实现　🟡 部分　⬜ 规划中

```
backend/
├── config/                     ✅ settings(.env/DRF Token/CORS/护栏) + urls + 健康检查
├── core/                       ✅ 安全核心（含单测）
│   ├── sql_guard.py            ✅ 只读 SQL 校验
│   ├── oracle_client.py        ✅ 绑定变量 + 流式 fetch + 行数上限 + 超时
│   ├── excel.py                ✅ openpyxl 流式导出
│   └── crypto.py               ✅ Fernet 加解密
├── apps/                       🟡 业务应用（v0.06 模型层；API/视图随 v0.08+）
│   ├── accounts/               ✅ 自定义 User（超管 / 辅助管理员 / 老板 角色）
│   ├── catalog/                ✅ Department / Category（部门 → 分类）
│   ├── datasource/             ✅ DataSource（密码 Fernet 加密）
│   ├── dataset/                ✅ Dataset（SQL / 归属分类 / 数据源 / 定时）
│   ├── execution/              ✅ Execution（执行记录 / 文件版本）
│   └── permission/             ✅ DepartmentMembership / Grant + can_view_dataset 可见性判定
└── tests/                      ✅ sql_guard / excel / permission（35 用例）

frontend/                       🟡 v0.07（双布局 + 角色分流，浅色令牌）
├── src/style.css               ✅ 浅色设计令牌
├── src/api/http.ts             ✅ axios（Token / 401 / 错误提示）
├── src/stores/auth.ts          ✅ 登录态 + 角色(profile/isManager)
├── src/router/index.ts         ✅ 路由 + 登录守卫 + 角色分流(requiresManager)
├── src/layouts/AdminLayout.vue ✅ 管理端（侧边菜单工作台）
├── src/layouts/UserLayout.vue  ✅ 用户端（门户顶栏，商务风）
└── src/views/
    ├── admin/                  🟡 home / 数据源 / 数据集 / 目录 / 权限 / 执行（占位）
    └── user/CatalogHome.vue    🟡 数据门户首页（占位）
```

> 登录后按角色分流：超管/辅助管理员 → `/admin`；普通用户 → `/`（用户端门户）。

> APScheduler 定时调度在数据集运行（v0.09+）后接入（见技术方案 §8.2 / §10.1）。

---

## 4. 数据模型（v0.06 已落地，迁移为准）

```
DataSource（Oracle 连接，密码加密）─┐
Department ─< Category ─< Dataset >─┘  ─< Execution（文件版本）
User（is_superuser / is_assistant_admin / is_boss）
  ├─< DepartmentMembership（部门, role=总监/主管/成员, see_all_in_dept）
  └─< Grant（个人或角色组 → 分类或数据集）
```

- **权限唯一出口**：`apps/permission/services.py::can_view_dataset(user, dataset)`，默认拒绝；任何"列目录/看数据集/下载"都须走它（§技术方案 3.3）。
- 详细字段见技术方案 §6 与各 app 迁移文件。

---

## 5. 接口清单

| 路径 | 方法 | 用途 | 鉴权 | 状态 |
|---|---|---|---|---|
| `/api/health/` | GET | 健康检查 | 无 | ✅ |
| `/api/auth/token/` | POST | 账号密码换 Token | 无 | ✅ |
| `/api/auth/me/` | GET | 当前用户 + 角色（is_manager 等） | Token | ✅ |
| `/admin/` | - | Django 后台 | 登录 | ✅ |

> 业务接口（数据源/数据集/目录/执行/下载/权限）随 app 实现登记。

### 5.1 本地启动（后端，Windows）

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
# 质量检查：python -m ruff check . / python -m black . / python -m pytest
```

### 5.2 本地启动（前端）

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5179 ，/api 自动代理到后端 8000
```

> 一键启动：项目根目录 `.\start-dev.ps1`。测试账号 admin / admin12345。

---

## 6. 部署

- 生产：Linux（systemd / Docker，待定）；开发：本地 Windows，代码跨平台。

---

## 7. 变更记录指引

本文档每次架构/接口变更时更新；版本级变更说明见 `changelog/`。
