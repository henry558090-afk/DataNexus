#!/usr/bin/env bash
# ============================================================
# data-nexus 一键启动（Linux）—— 起两个进程：web(gunicorn) + 定时(scheduler)
# 用法：bash deploy/start.sh
# 可选环境变量：DN_HOST(默认0.0.0.0) DN_PORT(默认8000) DN_WORKERS(默认3)
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
GUNICORN="$VENV/bin/gunicorn"
LOGDIR="$BACKEND/logs"
RUNDIR="$BACKEND/run"

HOST="${DN_HOST:-0.0.0.0}"
PORT="${DN_PORT:-8000}"
WORKERS="${DN_WORKERS:-3}"

# —— 前置检查 ——
if [ ! -x "$PY" ]; then
  echo "❌ 没找到虚拟环境，请先执行： bash deploy/setup.sh"; exit 1
fi
if [ ! -f "$BACKEND/.env" ]; then
  echo "❌ 缺少 backend/.env，请先执行： bash deploy/setup.sh"; exit 1
fi

mkdir -p "$LOGDIR" "$RUNDIR"

# —— 若已在运行，先停 ——
bash "$ROOT/deploy/stop.sh" >/dev/null 2>&1 || true

cd "$BACKEND"
echo "==> 数据库迁移 + 收集静态（幂等）"
"$PY" manage.py migrate --noinput
"$PY" manage.py collectstatic --noinput >/dev/null

echo "==> 启动 web (gunicorn) :$PORT"
nohup "$GUNICORN" config.wsgi:application \
  --chdir "$BACKEND" --bind "$HOST:$PORT" --workers "$WORKERS" \
  --access-logfile "$LOGDIR/gunicorn-access.log" \
  --error-logfile "$LOGDIR/gunicorn-error.log" \
  >/dev/null 2>&1 &
echo $! > "$RUNDIR/web.pid"

echo "==> 启动 scheduler (定时跑数)"
nohup "$PY" manage.py runscheduler >"$LOGDIR/scheduler.log" 2>&1 &
echo $! > "$RUNDIR/scheduler.pid"

sleep 1
echo ""
echo "✅ 已启动："
echo "   web       → http://$HOST:$PORT   (pid $(cat "$RUNDIR/web.pid"))"
echo "   scheduler → 定时进程              (pid $(cat "$RUNDIR/scheduler.pid"))"
echo "   日志      → $LOGDIR/"
echo "   停止      → bash $ROOT/deploy/stop.sh"
