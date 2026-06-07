#!/usr/bin/env bash
# ============================================================
# data-nexus 一次性环境初始化（Linux）
# 作用：建 venv → 装后端依赖 → 构建前端 → 生成 .env(含密钥) → 迁移 → 收集静态
# 用法：bash deploy/setup.sh
# 前置：已装 python3.11+ / python3-venv / pip / nodejs18+ / npm / git
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"

echo "==> [1/5] 创建 Python 虚拟环境"
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi
"$PY" -m pip install --upgrade pip -q

echo "==> [2/5] 安装后端依赖（生产）"
"$PY" -m pip install -r "$BACKEND/requirements-prod.txt" -q

echo "==> [3/5] 构建前端（生成 frontend/dist）"
if command -v npm >/dev/null 2>&1; then
  (cd "$FRONTEND" && npm ci && npm run build)
else
  echo "    ⚠️ 未检测到 npm：请在本地 npm run build 后，把 frontend/dist 上传到服务器同位置"
fi

echo "==> [4/5] 准备 backend/.env"
if [ ! -f "$BACKEND/.env" ]; then
  SECRET="$("$PY" -c 'import secrets;print(secrets.token_urlsafe(50))')"
  FERNET="$("$PY" -c 'from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())')"
  cat > "$BACKEND/.env" <<EOF
# —— 自动生成，请按需修改 ALLOWED_HOSTS ——
SECRET_KEY=$SECRET
DEBUG=False
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=

# ⚠️ 加密数据源密码的钥匙，务必【单独备份】！丢失则已存数据源密码全部解不开
FERNET_KEY=$FERNET

# 取数安全护栏
QUERY_MAX_ROWS=100000
QUERY_TIMEOUT_SECONDS=60
QUERY_FETCH_SIZE=1000
EXECUTION_KEEP=20

# 平台元数据库：默认 SQLite（无需配置）。要复用现有 MySQL 就取消下行注释：
# DATABASE_URL=mysql://user:password@host:3306/datanexus
EOF
  echo "    ✅ 已生成 backend/.env"
  echo "    ⚠️⚠️ 请立刻备份这串 FERNET_KEY： $FERNET"
else
  echo "    backend/.env 已存在，跳过"
fi

echo "==> [5/5] 数据库迁移 + 收集静态资源"
(cd "$BACKEND" && "$PY" manage.py migrate --noinput && "$PY" manage.py collectstatic --noinput)

echo ""
echo "================  初始化完成  ================"
echo "下一步："
echo "  1) 创建管理员： $PY $BACKEND/manage.py createsuperuser"
echo "  2) 按需编辑   ： $BACKEND/.env  (ALLOWED_HOSTS 改成你的域名/IP；要用 MySQL 则填 DATABASE_URL)"
echo "  3) 一键启动   ： bash $ROOT/deploy/start.sh"
echo "=============================================="
