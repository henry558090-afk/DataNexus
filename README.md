# data-nexus 数据共享平台

> 轻量级企业内部数据门户。核心：**把 SQL 跑成 Excel，按部门/权限受控分发给团队下载**。
> 技术栈：Django + DRF / Vue 3 + Element Plus / APScheduler / SQLite（平台元数据）/ **Oracle + MySQL**（业务数据源）。

当前版本：**v0.16**（dev 分支，最小生产化）。本地访问前端 **http://localhost:5179**（后端 8010）。
生产部署见 [docs/部署.md](docs/部署.md)：**无需 Nginx/Docker/PG**，Django 一个进程发前端+API，另一个进程跑定时。

---

## 功能一览

| 模块 | 能力 |
|---|---|
| 数据源 | Oracle / MySQL 连接管理，密码加密存储，连接测试 |
| 数据集 | 写只读 SQL → 预览前 50 行 → 运行生成 Excel；可归类到「部门/分类」 |
| 定时 | 手动 / 每隔 N 分钟 / 每天 HH:MM / Cron，自动跑数（`runscheduler` 进程） |
| 取数安全 | 只读校验 + 绑定变量 + 流式 fetch + 行数上限 + 查询超时 |
| 用户端门户 | 部门/分类树 + 搜索 + 数据卡片；详情看最新/历史并下载 |
| 权限 | 管理角色（超管/辅助管理员）+ 数据可见（老板/总监/主管/成员）+ 授权，默认拒绝 |
| 受控下载 | 登录鉴权 + 可见性校验 + 流式 + 中文文件名；执行历史保留清理 |
| 审计 | 登录 / 运行 / 下载全程留痕（账号/对象/IP/时间），管理端可查 |

---

## 快速开始（本地，Windows）

```powershell
# 一键启动（前后端各开一个窗口）
cd E:\data-nexus
.\start-dev.ps1
# 浏览器打开 http://localhost:5179  （默认账号 admin / admin12345）

# 定时调度（可选，单独进程）
cd backend
.\.venv\Scripts\python.exe manage.py runscheduler
```

> 后端开发端口 **8010**，前端 **5179**。质量检查：后端 `pytest`/`ruff`/`black`，前端 `npm run build`/`npm run lint`。

---

## 目录结构

| 路径 | 作用 |
|---|---|
| `README.md` | 项目总入口 |
| `docs/技术方案.md` | 技术选型与架构设计（含产品形态、角色权限、下载体验、里程碑） |
| `docs/开发规范.md` | 开发约束（需求/变更/删除/三维度审核/安全/Git/测试/文档） |
| `changelog/` | 每个版本的变更说明 + 下版计划（含版本索引） |
| `system-docs/architecture.md` | 当前系统真实架构快照 |
| `backend/` | Django + DRF 后端（apps：accounts/catalog/datasource/dataset/execution/permission/audit；core：db/scheduler/excel/crypto/sql_guard/pagination） |
| `frontend/` | Vue 3 + TS + Element Plus（双布局：管理端 / 用户端门户） |
| `start-dev.ps1` | 一键启动脚本 |

---

## 文档怎么配合

- **为什么这么设计** → `docs/技术方案.md`
- **开发守什么规矩** → `docs/开发规范.md`
- **现在系统长什么样** → `system-docs/architecture.md`
- **每版改了啥、下一步** → `changelog/`

> 规则：每完成一个版本（v0.01 起依次累计、不跨版本），同步更新 `changelog/` 与 `system-docs/`。

---

## 进度

| 阶段 | 版本 | 状态 |
|---|---|---|
| 文档与治理基线 | v0.01 | ✅ |
| 后端安全核心 / 前端骨架 / 登录 / 浅色 UI | v0.02–v0.05 | ✅ |
| 重构基线：数据模型/权限、双布局、数据源、SQL→Excel 闭环 | v0.06–v0.09 | ✅ |
| 审查加固、目录+用户门户、用户与权限 | v0.10–v0.12 | ✅ |
| MySQL、首页/门户重构、定时、保留、审计、分页、安全加固 | v0.13–v0.15 | ✅ |
| 数据分析报告（Word）/ 推送订阅 | v2 大版本 | ⬜ 规划 |

> 上线（最小方案，见 [docs/部署.md](docs/部署.md)）：填生产 `.env`（重生成密钥、**FERNET_KEY 要备份**、`DEBUG=False`、`ALLOWED_HOSTS`）→ `npm run build` → `migrate`/`collectstatic`/`createsuperuser` → 起 `gunicorn` + `runscheduler` 两个进程。再提供真实 Oracle/MySQL 只读账号做端到端验证。
