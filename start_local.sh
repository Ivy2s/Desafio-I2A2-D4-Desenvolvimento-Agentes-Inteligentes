#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-18005}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-15179}"
API_URL="http://${API_HOST}:${API_PORT}"

if [[ -x "${ROOT_DIR}/.venv-qa/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-qa/bin/python"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
  if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Erro: Python 3.11 ou superior não foi encontrado.' >&2
    exit 1
  fi
  printf '%s\n' 'Preparando ambiente virtual Python...'
  python3 -m venv "${ROOT_DIR}/.venv"
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
fi

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
  printf '%s\n' 'Erro: este projeto requer Python 3.11 ou superior.' >&2
  exit 1
fi

if ! "${PYTHON_BIN}" -c 'import dotenv, fastapi, langchain_core, langchain_google_genai, langchain_groq, multipart, pandas, uvicorn' >/dev/null 2>&1; then
  printf '%s\n' 'Instalando dependências Python...'
  "${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/requirements.txt"
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  printf '%s\n' 'Erro: Node.js 20+ e npm não foram encontrados.' >&2
  exit 1
fi

if ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)'; then
  printf '%s\n' 'Erro: este projeto requer Node.js 20 ou superior.' >&2
  exit 1
fi

if [[ ! -x "${ROOT_DIR}/frontend/node_modules/.bin/vite" ]]; then
  printf '%s\n' 'Instalando dependências do frontend...'
  npm --prefix "${ROOT_DIR}/frontend" ci
fi

CONFIG_ERROR="$("${PYTHON_BIN}" -c 'from services.config import ai_configuration_error; print(ai_configuration_error() or "")')"
if [[ -n "${CONFIG_ERROR}" ]]; then
  printf 'Erro de configuração: %s\n' "${CONFIG_ERROR}" >&2
  printf '%s\n' 'Copie .env.example para .env e informe uma chave válida.' >&2
  exit 1
fi

api_is_healthy() {
  "${PYTHON_BIN}" -c 'import sys, urllib.request; urllib.request.urlopen(sys.argv[1], timeout=1)' "${API_URL}/api/health" >/dev/null 2>&1
}

if api_is_healthy; then
  printf 'Erro: já existe uma API respondendo em %s\n' "${API_URL}" >&2
  exit 1
fi

cleanup() {
  trap - EXIT INT TERM
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${API_PID:-}" ]]; then
    kill "${API_PID}" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

"${PYTHON_BIN}" -m uvicorn api.main:app \
  --host "${API_HOST}" \
  --port "${API_PORT}" &
API_PID=$!

for _ in {1..60}; do
  if api_is_healthy; then
    break
  fi
  sleep 0.5
done

if ! api_is_healthy; then
  printf 'Erro: a API não iniciou em %s\n' "${API_URL}" >&2
  exit 1
fi

(
  cd "${ROOT_DIR}/frontend"
  exec env VITE_API_PROXY_TARGET="${API_URL}" \
    "${ROOT_DIR}/frontend/node_modules/.bin/vite" \
    --host "${FRONTEND_HOST}" \
    --port "${FRONTEND_PORT}"
) &
FRONTEND_PID=$!

printf 'Frontend: http://%s:%s\n' "${FRONTEND_HOST}" "${FRONTEND_PORT}"
printf 'Backend:  %s\n' "${API_URL}"
printf '%s\n' 'Pressione Ctrl+C para encerrar frontend e backend.'

wait "${API_PID}" "${FRONTEND_PID}"
