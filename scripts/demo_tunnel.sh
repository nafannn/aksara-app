#!/usr/bin/env bash
# Demo AKSARA dari laptop: satu URL HTTPS (Cloudflare Quick Tunnel) yang menyajikan
# frontend + API dari origin yang sama. Tanpa akun, tanpa kartu, tanpa CORS.
#
#   bash scripts/demo_tunnel.sh
#
# Ctrl+C menghentikan server dan tunnel sekaligus.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${AKSARA_DEMO_PORT:-18080}"
PY="${AKSARA_PYTHON:-$ROOT/vision/.venv/Scripts/python.exe}"
[[ -x "$PY" ]] || PY="python"

cd "$ROOT"

echo "== 1/3 build frontend (API relatif, satu origin) =="
VITE_API_URL=/api/recognize npm --prefix frontend run build >/dev/null
echo "   selesai: frontend/dist"

echo "== 2/3 jalankan backend + frontend di port $PORT =="
AKSARA_SERVE_FRONTEND=1 \
AKSARA_CORS_ORIGIN="*" \
PORT="$PORT" \
  "$PY" -m backend.app >"${TMPDIR:-/tmp}/aksara-demo.log" 2>&1 &
SERVER_PID=$!

cleanup() {
  echo
  echo "== berhenti =="
  [[ -n "${TUNNEL_PID:-}" ]] && kill "$TUNNEL_PID" 2>/dev/null || true
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

for _ in $(seq 1 60); do
  if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1; then break; fi
  sleep 2
done
curl -fsS --max-time 5 "http://127.0.0.1:$PORT/healthz" >/dev/null || {
  echo "backend gagal start; lihat ${TMPDIR:-/tmp}/aksara-demo.log" >&2
  exit 1
}

echo "== 3/3 buka tunnel publik =="
# Tunnel bernama diambil dari config cloudflared kalau env tidak diisi, supaya
# cukup `bash scripts/demo_tunnel.sh` untuk demo sehari-hari.
CONFIG="${AKSARA_CLOUDFLARED_CONFIG:-$HOME/.cloudflared/config.yml}"
NAMED_TUNNEL="${AKSARA_TUNNEL:-}"
PUBLIC_URL="${AKSARA_PUBLIC_URL:-}"
if [[ -z "$NAMED_TUNNEL" && -f "$CONFIG" ]]; then
  NAMED_TUNNEL="$(grep -E '^tunnel:' "$CONFIG" | head -1 | sed -E 's/^tunnel:[[:space:]]*//' || true)"
  if [[ -z "$PUBLIC_URL" ]]; then
    HOST="$(grep -E '^[[:space:]]*-[[:space:]]*hostname:' "$CONFIG" | head -1 | sed -E 's/.*hostname:[[:space:]]*//' || true)"
    [[ -n "$HOST" ]] && PUBLIC_URL="https://$HOST"
  fi
fi

if [[ -n "$NAMED_TUNNEL" && -n "$PUBLIC_URL" ]]; then
  echo "   tunnel bernama: $NAMED_TUNNEL -> $PUBLIC_URL"
  cloudflared tunnel run "$NAMED_TUNNEL" >"${TMPDIR:-/tmp}/aksara-tunnel.log" 2>&1 &
  TUNNEL_PID=$!
  URL="$PUBLIC_URL"
else
  cloudflared tunnel --url "http://localhost:$PORT" --no-autoupdate >"${TMPDIR:-/tmp}/aksara-tunnel.log" 2>&1 &
  TUNNEL_PID=$!
  URL=""
  for _ in $(seq 1 40); do
    URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "${TMPDIR:-/tmp}/aksara-tunnel.log" | head -1 || true)"
    [[ -n "$URL" ]] && break
    sleep 2
  done
  if [[ -z "$URL" ]]; then
    echo "tunnel tidak memberi URL; lihat ${TMPDIR:-/tmp}/aksara-tunnel.log" >&2
    exit 1
  fi
fi

cat <<EOF

=====================================================================
  Buka di ponsel:   $URL
  API sekaligus di: $URL/api/recognize
---------------------------------------------------------------------
  Kamera jalan karena URL-nya HTTPS (syarat getUserMedia).
  Selama sesi ini laptop harus hidup dan tidak sleep.
  Ctrl+C untuk menghentikan server dan tunnel.
=====================================================================
EOF

wait "$SERVER_PID"
