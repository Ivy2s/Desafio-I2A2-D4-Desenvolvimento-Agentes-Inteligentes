# QA Final

## Ambiente

- Linux; Python 3.12.3; Node/npm conforme ambiente local.
- Chromium Playwright 151.0.7922.34.
- A chave Gemini está em `.env` ignorado e não foi versionada.

## Git

- Branch: `feat/frontend-ui`
- HEAD inicial: `7196eec chore(frontend): remove production mocks and polish integration`
- HEAD final: `f5747db chore: finalize challenge QA and delivery package`
- Push/PR: não realizados

## Suítes

- Backend: `python3 -m pytest -q` -> `48 passed`.
- Frontend: Vitest `31 passed`; lint PASS; build PASS.
- Playwright Chromium: houve execução estável com 3 passed, incluindo upload ZIP+dicionário, formato inválido e uma query Gemini real; a repetição final terminou 2 passed/1 failed por quota Gemini 429.
- Playwright mobile 320 px: upload e formato inválido passaram; a consulta real também fica condicionada à quota externa.
- `npm audit --audit-level=moderate`: 0 vulnerabilidades.
- `pip check`: dependência global externa (`repolib` requer `gnupg`); requisitos do projeto instalados.

## Evidências

O E2E usa `setInputFiles`, FastAPI real, Vite real e nenhum mock de sucesso.
O count real retornou 7 registros totais, incluindo 4 em `compras`. A tentativa de executar quatro
perguntas reais consecutivas expirou no segundo request Gemini, portanto as
quatro respostas, tabela e gráfico não têm evidência real suficiente.

## Segurança e qualidade

Traversal, symlink, limites ZIP, isolamento, UUID, validação e limpeza estão
cobertos por backend. `.env`, `node_modules`, `.runtime` e caches não entram no
Git/ZIP de código. O frontend mantém a chave apenas no backend.

## Status

`DELIVERY_BLOCKED`

Bloqueio objetivo: a credencial atingiu quota gratuita Gemini (`429
ResourceExhausted`) ao repetir as consultas. É necessário usar credencial/quota
estável, repetir as quatro perguntas e capturar respostas reais de texto, tabela
e gráfico. Não declarar
`REAL_GEMINI_E2E = PASS` enquanto isso não ocorrer.
