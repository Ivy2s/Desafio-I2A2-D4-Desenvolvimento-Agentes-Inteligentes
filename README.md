
<table border="0">
  <tr>
    <td width="220" align="center" valign="middle">
      <img src="imagens/Agente Inteligente.avif"="200">
    </td>
    <td valign="middle">
      <h1>Projeto Agente Inteligente com consulta de base de dados CSV</h1>
    </td>
  </tr>
</table>

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## 📖 Visão Geral

Este é um projeto de **agentes inteligentes** capazes de responderem perguntas em linguagem natural usando um conjunto de dados armazenados em arquivos CSV.

  
## 🎯 Objetivo

Demonstrar como a **inteligência agêntica** pode ser utilizada para transformar dados estruturados em informações de inteligência competitiva. Por meio de **agentes inteligentes** que aplicam conceitos de LLMs, ferramentas (tools), orquestração e automação, é possível que a solução interprete as perguntas do usuário e produza respostas úteis a partir de dados carregados de uma base de conhecimento.

---
## 💻 Frameworks e Ferramentas

O projeto foi desenvolvido em **Python**, **LangChain**, **Pydantic AI**
Nota: Listar outras tecnologias e frameworks utilizados


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

## ⚙️ Descrição dos Agentes do projeto

Nota: descrever os agentes desenvolvidos (item obrigatório)

## ⚙️ Fluxo de Funcionamento da Aplicação

  <img src="imagens/Aplicação Decision Flow-2026-08-16-020105.png"="200">
  



---

## 📁 Estrutura do Repositório

O repositório está organizado nas seguintes pastas:

| Diretório | Conteúdo |
| :--- | :--- |
| `Agente-csv/` | Contém trabalho do projeto. |
| `Agentes/` | Prompt do agente. |
| `Data/` | Conjunto de dados brutos e/ou processados utilizados no projeto. |
| `Docs/` | Dicionário de dados e documentação da arquitetura de trabalho do projeto. |
| `Imagens/` | Imagens usadas no projeto. |
| `Pipeline/` | Carregamento e gerenciamento dos CSVs de trabalho do projeto. |
| `Services/` | Contém o trabalho do projeto. |
| `Tests/` | Testes de validação do funcionamento. |
| `Tools/` | Consulta aos dados. |
| `README.md` | Este arquivo. |


## 📈 Dados de teste

Os datasets fornecidos pelo curso Insurminds da I2A2 não são versionados neste repositório devido ao tamanho dos arquivos.

Para testar localmente:

1. Baixe os datasets disponibilizados pelo curso.
2. Coloque o ZIP em `data/raw/`.
3. Execute a aplicação.
4. Faça o upload do ZIP pela Interface A.


## 📄 Documento do Projeto

Nota: Referenciar o report final
