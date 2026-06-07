# DESIGN.md — data-nexus 设计系统

> 由 impeccable 规范（product register）落地。令牌定义在 `frontend/src/style.css`。

## 字体
- 一套 sans：`Inter` + 系统/中文回退。产品 UI 不做 display/body 配对。
- 固定 rem 字阶（非 fluid clamp），比率 ~1.2：12 / 13 / **14(base)** / 16 / 18 / 22 / 28px。层次靠**字重 + 字号**，不靠多字体。

## 配色（浅色系，克制 = Restrained）
| 角色 | 值 | 用途 |
|---|---|---|
| `--bg` | #f5f7fb | 应用底（冷调浅） |
| `--surface` | #ffffff | 内容面 |
| `--surface-2` | #f9fafd | 第二中性层：侧栏/工具栏/面板 |
| `--border` / `--border-strong` | #e9edf4 / #d8deea | 描边 |
| `--ink` | #1a1f2b | 主文本 |
| `--ink-2` | #565f70 | 次文本（对白 ≥4.5:1，正文可用） |
| `--ink-3` | #889. | 元信息（仅非关键，时间/字节） |
| `--accent` | #4b5bd6 | 主操作/当前选中/状态（**不做装饰**） |
| `--accent-weak` | #eef0fc | 选中底色 |
| 语义 | success #16a34a / danger #dc2626 / warning #d97706 | 状态 |

- 一个强调色，锁定全站；强调色只出现在主按钮、当前选中、状态指示。
- 阴影 tint 到墨色（非纯黑）；圆角统一一套（sm 8 / base 12 / lg 16 / pill）。

## 动效（服务状态，不装饰）
- `--ease-out: cubic-bezier(0.22, 1, 0.36, 1)`；`--dur-fast 140ms` / `--dur 200ms`。
- 用在：hover 反馈、选中过渡、列表进入（轻微 stagger）、骨架屏、展开收起。**不做开场编排**。
- **必带** `@media (prefers-reduced-motion: reduce)` 关闭。

## 组件态
每个可交互组件都要 default / hover / focus(可见焦点环) / active(下压 1px) / disabled / loading（骨架，非转圈）。空状态要"教用户怎么用"。

## 布局
响应式靠结构（侧栏收起、表格响应、断点列数），不靠 fluid 字号。内容容器 max-width 1280。
