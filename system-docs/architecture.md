# data-nexus 当前系统架构

> 本文件是**当前系统的真实快照**，随代码变更同步更新（开发规范第 8 节）。
> 最近更新：2026-06-06　|　对应版本：**v0.15**（审计日志 + 列表分页 + 生产安全加固，dev 分支）

---

## 1. 当前状态

| 阶段 | 状态 |
|---|---|
| 技术方案 | ✅ 已定稿（见 docs/技术方案.md v0.4） |
| 开发规范 | ✅ 已定稿（见 docs/开发规范.md v1.1） |
| 后端代码 | 🟢 全链路 + 双库 + **定时调度 + 历史保留 + 审计 + 分页 + 安全加固**（v0.15，79 测试） |
| 前端代码 | 🟢 管理端(首页/数据源/数据集含定时/目录/权限/**审计**) + 用户端门户（v0.15） |

> 当前在 `dev` 分支进行「重构基线」大改版（v0.06 起）。后端模型已落地，API 与前端重构随后续版本推进。

---

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Django + DRF |
| 调度 | **APScheduler（单进程，runscheduler 命令）** —— 已接入 |
| 元数据库 | SQLite |
| 业务数据源 | **Oracle（oracledb thin）/ MySQL（PyMySQL）** —— core/db.py 统一 |
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
│   ├── db.py                   ✅ Oracle/MySQL 统一取数（绑定变量+流式+行数上限+超时）
│   ├── excel.py                ✅ openpyxl 流式导出
│   └── crypto.py               ✅ Fernet 加解密
├── apps/                       🟡 业务应用（v0.06 模型层；API/视图随 v0.08+）
│   ├── accounts/               ✅ 自定义 User（超管 / 辅助管理员 / 老板 角色）
│   ├── catalog/                ✅ Department / Category（部门 → 分类）
│   ├── datasource/             ✅ DataSource + API（CRUD/测试连接，仅管理员）
│   ├── dataset/                ✅ Dataset + API（CRUD/预览/运行→Excel；services.run_dataset；category 可空=未归类）
│   ├── execution/              ✅ Execution + API（列表/下载，FileResponse 流式）
│   ├── permission/             ✅ DepartmentMembership / Grant + can_view_dataset 可见性判定
│   └── audit/                  ✅ AuditLog + log()（登录/运行/下载留痕）
core/ 另含：db.py(双库取数) / scheduler.py(定时) / pagination.py / excel / crypto / sql_guard
└── tests/                      ✅ sql_guard / excel / permission（35 用例）

frontend/                       🟡 v0.07（双布局 + 角色分流，浅色令牌）
├── src/style.css               ✅ 浅色设计令牌
├── src/api/http.ts             ✅ axios（Token / 401 / 错误提示）
├── src/stores/auth.ts          ✅ 登录态 + 角色(profile/isManager)
├── src/router/index.ts         ✅ 路由 + 登录守卫 + 角色分流(requiresManager)
├── src/layouts/AdminLayout.vue ✅ 管理端（侧边菜单工作台）
├── src/layouts/UserLayout.vue  ✅ 用户端（门户顶栏，商务风）
└── src/views/
    ├── admin/                  ✅ home/数据源/数据集(SQL/预览/运行)/执行/目录管理/用户与权限
    │                              user/  ✅ 门户 CatalogHome(卡片墙) + DatasetDetail(最新/历史/下载)
    └── user/CatalogHome.vue    🟡 数据门户首页（占位）

（前端新增 api/datasource.ts 封装数据源接口）
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
| `/api/stats/` | GET | 管理端首页统计（数据源/数据集/执行/今日） | 管理员 | ✅ |
| `/api/datasources/` | GET/POST | 数据源列表/新建 | 管理员 | ✅ |
| `/api/datasources/{id}/` | GET/PATCH/DELETE | 数据源详情/改/删 | 管理员 | ✅ |
| `/api/datasources/{id}/test/` | POST | 测试已保存数据源连接 | 管理员 | ✅ |
| `/api/datasources/test-connection/` | POST | 用表单参数预检连接 | 管理员 | ✅ |
| `/api/datasets/` `/{id}/` | GET/POST/PATCH/DELETE | 数据集 CRUD（SQL 保存即校验只读） | 管理员 | ✅ |
| `/api/datasets/{id}/preview/` | POST | 预览前 50 行 | 管理员 | ✅ |
| `/api/datasets/{id}/run/` | POST | 运行 → 生成 Excel | 管理员 | ✅ |
| `/api/executions/` | GET | 执行记录（?dataset 过滤） | 管理员 | ✅ |
| `/api/executions/{id}/download/` | GET | 下载 Excel（流式 + 中文名 RFC5987） | 管理员 | ✅ |
| `/api/departments/` `/categories/` | CRUD | 部门 / 分类管理 | 管理员 | ✅ |
| `/api/portal/tree/` | GET | 用户可见的目录树（部门→分类→数据集） | 登录 | ✅ |
| `/api/portal/datasets/{id}/` | GET | 数据集详情（最新+历史，含可见性校验） | 登录 | ✅ |
| `/api/portal/executions/{id}/download/` | GET | 用户下载（含可见性校验） | 登录 | ✅ |
| `/api/users/` | CRUD | 用户管理 + 角色（辅助管理员看不到超管） | 管理员 | ✅ |
| `/api/memberships/` | CRUD | 部门成员（总监/主管/成员 + 看全部） | 管理员 | ✅ |
| `/api/grants/` | CRUD | 成员授权（个人/角色组 → 分类/数据集） | 管理员 | ✅ |
| `/api/audit-logs/` | GET | 审计日志（分页，?action/?user 过滤） | 管理员 | ✅ |
| `/admin/` | - | Django 后台 | 登录 | ✅ |

> 列表分页：`/api/executions/`、`/api/audit-logs/` 返回 `{count,next,previous,results}`（page_size=20）；其余列表为完整数组。
> 审计：登录、运行数据集、下载文件均留痕（账号/动作/对象/IP/时间）。

> 数据源密码 write_only，永不回显；接口仅管理员（IsManager）。其余业务接口随 app 实现登记。

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
- **定时调度**：另起单进程 `python manage.py runscheduler`（每 30s 同步数据集 cron/interval；须仅一个实例，见技术方案 §10.1）。
- **执行历史保留**：每数据集保留最近 `EXECUTION_KEEP`（默认 20）次，超出连同文件自动清理。

---

## 7. 变更记录指引

本文档每次架构/接口变更时更新；版本级变更说明见 `changelog/`。
