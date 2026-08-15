# QA Final

## Ambiente

- Linux; Python 3.12.3; Node/npm local; Chromium Playwright 151.0.7922.34.
- Backend e Vite foram iniciados pelo `playwright.config.ts`.
- `.env` é ignorado e as chaves não foram versionadas.

## Git

- Branch: `feat/frontend-ui`
- HEAD inicial: `6351c82 docs: record Groq E2E evidence`
- HEAD final: será registrado no commit final desta certificação
- Push/PR: não realizados

## Suítes

- Backend: `.venv-qa/bin/python -m pytest -q` -> `49 passed`.
- Frontend: Vitest `31 passed`; lint PASS; build PASS.
- `pip check`: PASS em `.venv-qa` (`No broken requirements found`).
- `npm audit --audit-level=moderate`: 0 vulnerabilidades.
- Playwright core serial com Chromium/Groq `llama-3.1-8b-instant`: upload, dicionário e quatro perguntas reais passaram individualmente.
- Playwright completo Chromium + mobile 320: `14 passed`, com `workers: 1` para evitar consumo concorrente da quota Groq.

## Evidências reais

O E2E usa `setInputFiles`, FastAPI real, Vite real e nenhum mock de sucesso. O ZIP contém `compras.csv`, `fornecedores.csv` e `dicionario.csv`. As quatro perguntas foram executadas em cenários Playwright independentes:

| Pergunta | Esperado | Aplicação | Resultado |
| --- | --- | --- | --- |
| Registros em `compras` | 4 | 4 | PASS |
| Soma de `valor` por `fornecedor` | Alfa 3500, Beta 1500, Gamma 1000 | Valores exibidos em texto/tabela | PASS |
| Linhas de `compras` ordenadas por `valor` | Monitor 2500 no topo | Tabela real com Monitor/2500 | PASS |
| Registros em `fornecedores` | 3 | 3 | PASS |

## Formatos e UX

- Texto: PASS, resposta `answer` e contagens reais.
- Tabela: PASS, headers/linhas reais em `DataTable`.
- Gráfico: PASS, SVG derivado da resposta tabular de agregação.
- Interface A/B, ZIP, erro de extensão, loading, endpoint real e mobile 320 foram exercitados.

## Segurança

Traversal, symlink, limites ZIP, isolamento UUID, validação, limpeza, erros de API e ausência de segredo no frontend estão cobertos pelo backend. O ZIP final não inclui `.env`, `.git`, `node_modules`, ambientes virtuais ou caches.

## Provedor de certificação

O provedor selecionado para esta certificação foi Groq, com a nova chave fornecida e `llama-3.1-8b-instant`. Gemini não foi usado neste teste. O agente real, tools, dados e respostas foram comprovados no navegador contra FastAPI real. Estado formal: `DELIVERY_CERTIFIED`.

## Artefatos

`docs/challenge_compliance_matrix.md`, `deliverables/relatorio_tecnico_desafio_4.md`, PDF, `CHECKLIST_ENTREGA.md`, screenshots em `deliverables/evidence/` e ZIP de código-fonte.
