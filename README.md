# data-nexus 数据共享平台

> 轻量级企业内部数据共享平台。核心：**把 SQL 跑成 Excel，提供受控下载**。
> 技术栈：Django + DRF / Vue 3 + Element Plus / APScheduler / SQLite / Oracle。

当前版本：**v0.01**（文档与治理基线，代码未开始）。

---

## 目录结构与各文件作用

| 路径 | 作用 |
|---|---|
| `README.md` | **项目总入口**：是什么、目录结构、各文件作用、如何上手 |
| `.gitignore` | Git 忽略规则：隔离 `.env`、密钥、依赖、生成产物等，不进仓库 |
| `.gitattributes` | 统一换行符为 LF，避免 Windows 开发 / Linux 部署的 CRLF 问题 |
| `docs/技术方案.md` | **技术选型与架构设计**（长期方案，主体稳定、可微调） |
| `docs/开发规范.md` | **开发约束**（AI 据此开发，团队共同遵守）：需求/变更/删除/三维度审核/安全/Git/测试/文档 |
| `changelog/` | **每个版本的变更说明 + 下版计划**（每完成一个版本必更新） |
| `changelog/README.md` | 该目录说明与版本索引 |
| `changelog/template.md` | 版本变更说明的模板，新建版本复制改名 |
| `changelog/v0.01.md` | v0.01 版本的变更说明 |
| `system-docs/architecture.md` | **当前系统真实架构快照**（每次架构/接口变更必更新） |
| `backend/`（待建） | Django + DRF 后端 |
| `frontend/`（待建） | Vue 3 + Element Plus 前端 |

---

## 文档怎么配合（重要）

- **要了解"为什么这么设计"** → 看 `docs/技术方案.md`
- **要了解"开发要守什么规矩"** → 看 `docs/开发规范.md`
- **要了解"现在系统长什么样"** → 看 `system-docs/architecture.md`
- **要了解"每个版本改了啥、下一步做啥"** → 看 `changelog/`

> 规则：每完成一个版本（从 v0.01 起依次累计、不跨版本），**必须同步更新「changelog」与「system-docs」**。

---

## 路线图

| 阶段 | 内容 |
|---|---|
| v1（核心） | 配 Oracle 数据源 → 写 SQL 任务 → 跑 → 出 Excel → 受控下载 |
| v2（大版本） | 数据分析报告（SQL → 报告） |
