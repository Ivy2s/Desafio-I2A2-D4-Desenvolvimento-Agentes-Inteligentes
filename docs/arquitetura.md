                ┌─────────────────────┐
                │   INTERFACE A       │
                │ Upload de ZIP       │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │      PIPELINE       │
                │                     │
                │ ZIP → CSV → dados  │
                │ validação           │
                │ dicionário          │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │      AGENTE         │
                │                     │
                │ Pergunta natural    │
                │       ↓             │
                │ interpreta intenção │
                │       ↓             │
                │ chama TOOL          │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ CONSULTA AOS DADOS │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │   INTERFACE B       │
                │ resposta            │
                │ texto/tabela/gráfico│
                └─────────────────────┘


UPLOAD
   ↓
qualquer ZIP compatível
   ↓
pipeline descobre datasets
   ↓
DataDictionary descreve os datasets
   ↓
agente recebe essa informação
   ↓
agente decide qual dataset/coluna utilizar