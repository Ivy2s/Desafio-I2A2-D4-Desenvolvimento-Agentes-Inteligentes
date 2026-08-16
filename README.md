
<table border="0">
  <tr>
    <td width="420" align="center" valign="middle">
      <img src="imagens/Agente Inteligente.avif"="420">
    </td>
    <td valign="middle">
      <h1>Projeto Agente Inteligente com consulta de base de dados CSV</h1>
    </td>
  </tr>
</table>




## 📖 Visão Geral

Este é um projeto de **agentes inteligentes** capazes de responderem perguntas em linguagem natural usando um conjunto de dados armazenados em arquivos CSV.


## 🎯 Objetivo

Demonstrar como a **inteligência agêntica** pode ser utilizada para transformar dados estruturados em informações de inteligência competitiva. Por meio de **agentes inteligentes** que aplicam conceitos de LLMs, ferramentas (tools), orquestração e automação, é possível que a solução interprete as perguntas do usuário e produza respostas úteis a partir de dados carregados de uma base de conhecimento.

---
## 💻 Frameworks e Ferramentas

O projeto foi desenvolvido em **Python**, **LangChain**, **Pydantic AI**.



## 🛠️ Arquitetura

            ┌─────────────────────┐
            │   INTERFACE A       │
            │ Upload de ZIP       │
            └──────────┬──────────┘
                       ↓
            ┌─────────────────────┐
            │      PIPELINE       │
            │                     │
            │ ZIP → CSV → Dados   │
            │ Validação           │
            │ Dicionário          │
            └──────────┬──────────┘
                       ↓
            ┌─────────────────────┐
            │      AGENTE         │
            │                     │
            │ Pergunta natural    │
            │          ↓          │
            │ Interpreta intenção │
            │          ↓          │
            │ Chama TOOL          │
            └──────────┬──────────┘
                       ↓
            ┌─────────────────────┐
            │ CONSULTA AOS DADOS  │
            └──────────┬──────────┘
                       ↓
            ┌─────────────────────┐
            │   INTERFACE B       │
            │ Resposta            │
            │ Texto/Tabela/Gráfico│
            └─────────────────────┘

UPLOAD ↓ qualquer ZIP compatível ↓ pipeline descobre datasets ↓ DataDictionary descreve os datasets ↓ agente recebe essa informação ↓ agente decide qual dataset/coluna utilizar

## 🤖 Descrição do Agente do projeto

**Data Assistent** é uma aplicação web para carregar arquivos CSV ou ZIP e consultar dados em linguagem natural. O frontend React envia os arquivos ao backend FastAPI; um agente do LangChain com Gemini ou Groq interpreta a pergunta, e o Pandas executa a consulta de forma determinística.


## ⚙️ Fluxo de Funcionamento da Aplicação

<table border="0">
  <tr>
    <td width="420" align="center" valign="middle">
  <img src="imagens/Aplicação Decision Flow-2026-08-16-020105.png"="400">
      </td>
    <td valign="middle">
       </td>
  </tr>
</table>



---

## 📁 Estrutura do Repositório

O repositório está organizado nas seguintes pastas:

| Diretório | Conteúdo |
| :--- | :--- |
| `Agentes/` | Prompts e agentes LangChain Gemini/Groq. |
| `API/` | Rotas e contratos FastAPI. |
| `Data/` | Conjunto de dados brutos e/ou processados utilizados no projeto. |
| `Docs/` | Dicionário de dados e documentação da arquitetura de trabalho do projeto. |
| `Frontend/` | React, interface de upload e workspace de consulta. |
| `Imagens/` | Imagens usadas no projeto. |
| `Pipeline/` | Extração segura, leitura, validação e consultas Pandas. |
| `Scripts/` | Query. |
| `Services/` | Sessões, consultas, providers e tratamento de erros. |
| `Tests/` | Testes de validação do funcionamento. |
| `Tools/` | Schemas e tools estruturadas. |
| `README.md` | Arquivo com objetivos e instruções do projeto. |


## 📈 Dados de teste

Os datasets fornecidos pelo curso Insurminds da I2A2 não são versionados neste repositório devido ao tamanho dos arquivos.

Para testar localmente:

1. Baixe os datasets disponibilizados pelo curso.
2. Coloque o ZIP em `data/raw/`.
3. Execute a aplicação.
4. Faça o upload do ZIP pela Interface A.


---

## 📝Requisitos

- Linux, macOS ou Windows com WSL/Git Bash;
- Python 3.11 ou superior com suporte a `venv`;
- Node.js 20 ou superior com `npm`;
- acesso à internet na primeira execução e para consultar o provedor de IA;
- uma chave válida do Gemini ou da Groq.

Em distribuições Debian/Ubuntu, instale o suporte a ambientes virtuais se ele
não estiver disponível:

```bash
sudo apt install python3-venv
```

## Início rápido

1. Clone o repositório e entre no diretório do projeto.
2. Crie o arquivo local de configuração:

```bash
cp .env.example .env
```

3. Abra `.env`, escolha um provedor e informe a respectiva chave.
4. Inicie a aplicação:

```bash
bash start_local.sh
```

Na primeira execução, o script cria `.venv`, instala `requirements.txt` e
executa `npm ci` no frontend. Nas execuções seguintes, essas etapas são
ignoradas quando as dependências já estão disponíveis.

Depois da inicialização, acesse:

- Interface: `http://127.0.0.1:15179`
- API: `http://127.0.0.1:18005`
- Health check: `http://127.0.0.1:18005/api/health`

Use `Ctrl+C` no terminal para encerrar frontend e backend.

## Configuração da IA

As chaves pertencem somente ao backend. Nunca use variáveis `VITE_*` para armazenar credenciais.

### Gemini

```env
AI_PROVIDER=gemini
GOOGLE_API_KEY=sua_chave
GEMINI_MODEL=gemini-flash-latest
```

### Groq

```env
AI_PROVIDER=groq
GROQ_API_KEY=sua_chave
GROQ_MODEL=openai/gpt-oss-20b
```

Se `AI_PROVIDER` for removido do `.env`, o sistema seleciona automaticamente o provedor cuja chave estiver preenchida. Quando as duas chaves existem, Gemini é o primário e Groq pode ser usado como fallback em falhas compatíveis.

O startup interrompe a execução com uma mensagem clara quando o provedor é inválido ou sua chave está ausente.

## Como usar

1. Abra a interface no navegador.
2. Arraste um `.csv` ou `.zip` para a área de upload, ou selecione o arquivo.
3. Clique em **Iniciar upload**.
4. Após o processamento, clique em **Explorar dados**.
5. Digite uma pergunta no chat e pressione `Enter`.

Cada upload cria uma sessão isolada por UUID. Os dados permanecem somente em memória e em `.runtime` durante a execução e são perdidos após o restart.

## Arquivos aceitos

### CSV

- extensões `.csv`;
- separadores vírgula, ponto e vírgula ou tabulação;
- encodings UTF-8, UTF-8 com BOM, Latin-1, ISO-8859-1 e CP1252;
- arquivo não vazio e com nomes de colunas únicos;
- limite padrão de upload de 500 MB.

Os nomes das colunas são normalizados para minúsculas, sem acentos e com espaços convertidos em `_`. Por exemplo, `VALOR NOTA FISCAL` torna-se `valor_nota_fiscal`.

### ZIP

O ZIP pode conter um ou mais CSVs, inclusive em subdiretórios. Ele deve conter pelo menos um CSV de dados. Arquivos com o mesmo nome-base não são permitidos, mesmo quando estão em pastas diferentes.

O backend rejeita ZIPs corrompidos, caminhos absolutos, path traversal,
symlinks, entradas duplicadas e arquivos que excedam os limites de segurança.

### Dicionário de dados opcional

O ZIP pode conter `dicionario.csv`, `data_dictionary.csv` ou `dictionary.csv`.
Esse arquivo deve possuir:

```csv
arquivo,coluna,descricao
compras.csv,valor_total,Valor total da compra em reais
compras.csv,fornecedor,Nome do fornecedor
```

O dicionário ajuda o agente a relacionar os termos da pergunta às colunas. Ele não é contado como dataset.

## Consultas suportadas

O agente suporta:

- contagem de registros;
- listagem de linhas, com ordenação crescente ou decrescente;
- soma, média, mínimo, máximo e contagem de valores;
- agrupamento por uma dimensão;
- rankings e top N;
- retorno da linha completa que possui o maior ou menor valor;
- resposta textual, tabela e gráfico quando a estrutura permitir.

Exemplos:

```text
Quantos registros existem neste dataset?
Qual é a soma da coluna valor_total?
Qual fornecedor possui a maior soma de valor_total?
Quais são os cinco maiores fornecedores por valor_total?
Liste os dez registros com maior valor_total.
Qual é o maior valor_total e qual registro possui esse valor?
Qual é a média de valor_total agrupada por uf_emitente?
```

O agente trabalha com os nomes e descrições encontrados no arquivo. Perguntas ambíguas podem exigir que o usuário informe o dataset ou a coluna desejada.

### Limites atuais

- não há joins entre CSVs;
- não há filtros arbitrários além do filtro especial por uma coluna `periodo`;
- perguntas de crescimento, comparação entre intervalos e fórmulas compostas
  podem não ser representáveis;
- gráficos são gerados para tabelas com uma dimensão, uma métrica numérica e no
  máximo 20 categorias;
- qualidade e disponibilidade também dependem do modelo e da quota do provedor.

## Portas e execução separada

Para alterar as portas:

```bash
API_PORT=18006 FRONTEND_PORT=15180 bash start_local.sh
```

Para executar os serviços manualmente:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 18005
```

Em outro terminal:

```bash
cd frontend
npm ci
VITE_API_PROXY_TARGET=http://127.0.0.1:18005 npm run dev -- --host 127.0.0.1 --port 15179
```

## API

| Método | Rota | Finalidade |
| --- | --- | --- |
| `GET` | `/api/health` | Estado da API e configuração da IA |
| `POST` | `/api/datasets` | Upload e processamento de CSV/ZIP |
| `GET` | `/api/datasets/{dataset_id}` | Metadados da sessão |
| `POST` | `/api/datasets/{dataset_id}/query` | Pergunta em linguagem natural |

## Testes

Backend:

```bash
.venv/bin/python -m pytest -q
```

Frontend:

```bash
cd frontend
npm test
npm run lint
npm run build
```

E2E com FastAPI, Vite e Chromium reais:

```bash
cd frontend
npx playwright install chromium
npm run e2e
```

As consultas E2E reais consomem quota do provedor configurado. Screenshots, traces e resultados temporários são gravados em `frontend/test-results/`.

## 📌 Solução de problemas

### Chave ausente ou provider inválido

Copie `.env.example` para `.env`, preencha uma chave e confirme que
`AI_PROVIDER` corresponde a ela.

### HTTP 429 ou limite de quota

Aguarde o tempo informado pelo provedor ou use outra chave/plano. O sistema não fabrica respostas quando o provedor bloqueia a consulta.

### Porta ocupada

```bash
API_PORT=18006 FRONTEND_PORT=15180 bash start_local.sh
```

### Dependências inconsistentes

Remova apenas os ambientes gerados e inicie novamente:

```bash
rm -rf .venv frontend/node_modules
bash start_local.sh
```

### Upload rejeitado

Confirme a extensão, o tamanho, o separador, o encoding, a existência de pelo menos uma linha e a ausência de colunas ou nomes de datasets duplicados.

## Arquitetura e segurança

- `frontend/`: React, interface de upload e workspace de consulta;
- `api/`: rotas e contratos FastAPI;
- `services/`: sessões, consultas, providers e tratamento de erros;
- `agents/`: prompts e agentes LangChain Gemini/Groq;
- `tools/`: schemas e tools estruturadas;
- `pipeline/`: extração segura, leitura, validação e consultas Pandas.

O arquivo `.env`, `.runtime`, ambientes virtuais, dependências e resultados de
teste são ignorados pelo Git. Não faça commit de chaves ou credenciais.

Consulte também `docs/arquitetura.md`, `docs/api_contract.md` e
`docs/challenge_compliance_matrix.md`.

## 📄 Documento do Projeto

Nota: Referenciar o report final
