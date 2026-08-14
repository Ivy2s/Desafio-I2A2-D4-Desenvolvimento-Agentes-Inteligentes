import type { DataAssistantGateway, DatasetSummary, QueryRequest, QueryResponse } from '../contracts/dataAssistant'

const wait = (duration: number) => new Promise((resolve) => window.setTimeout(resolve, duration))

const normalize = (value: string) => value.toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g, '')

const supplierRows = [
  { fornecedor: 'Metalúrgica Horizonte', valor: 184250.4 },
  { fornecedor: 'Distribuidora Vale Sul', valor: 139870.15 },
  { fornecedor: 'Comercial Nova Era', valor: 112430.9 },
  { fornecedor: 'Atacadão Central', valor: 98420.5 },
  { fornecedor: 'Papelaria Jatobá', valor: 76210.75 },
]

const monthRows = [
  { mes: 'Jan', total: 164200 }, { mes: 'Fev', total: 188450 }, { mes: 'Mar', total: 201300 },
  { mes: 'Abr', total: 235800 }, { mes: 'Mai', total: 249100 }, { mes: 'Jun', total: 277640 },
]

const productRows = [
  { produto: 'Bobina de aço 2mm', unidades: 8420 }, { produto: 'Cabo flexível 10mm', unidades: 6940 },
  { produto: 'Embalagem kraft 40cm', unidades: 5710 }, { produto: 'Conector industrial', unidades: 4380 },
]

export class MockDataAssistantGateway implements DataAssistantGateway {
  async uploadDataset(file: File): Promise<DatasetSummary> {
    await wait(1000)
    if (normalize(file.name).includes('falha')) throw new Error('Não foi possível preparar este arquivo de demonstração.')
    return {
      id: 'mock-dataset', name: file.name, csvFiles: ['NFe_Cabecalho.csv', 'NFe_Itens.csv', 'Dicionario.csv'],
      records: 128430, columns: 24, status: 'ready',
    }
  }

  async queryDataset(request: QueryRequest): Promise<QueryResponse> {
    await wait(1100)
    const question = normalize(request.question)
    if (question.includes('erro')) throw new Error('A consulta simulada não pôde ser concluída.')

    if (question.includes('fornecedor') && (question.includes('maior') || question.includes('cinco'))) {
      return {
        id: crypto.randomUUID(), question: request.question,
        answer: 'A Metalúrgica Horizonte concentrou o maior valor no período, com R$ 184.250,40. Os cinco maiores fornecedores representam 68,4% do total analisado.',
        table: { columns: ['fornecedor', 'valor'], rows: supplierRows },
        chart: { type: 'bar', title: 'Valor comprado por fornecedor', xKey: 'fornecedor', yKey: 'valor', data: supplierRows },
        metadata: { executionTimeMs: 1100, agent: 'mock fixture' },
      }
    }
    if (question.includes('produto') || question.includes('volume comprado')) {
      return {
        id: crypto.randomUUID(), question: request.question,
        answer: 'A Bobina de aço 2mm apresentou o maior volume comprado, com 8.420 unidades no período.',
        table: { columns: ['produto', 'unidades'], rows: productRows },
        metadata: { executionTimeMs: 1100, agent: 'mock fixture' },
      }
    }
    if (question.includes('mes') || question.includes('mês') || question.includes('gasto')) {
      return {
        id: crypto.randomUUID(), question: request.question,
        answer: 'O total mensal cresceu de forma contínua no recorte demonstrativo, chegando a R$ 277.640 em junho.',
        chart: { type: 'line', title: 'Total gasto por mês', xKey: 'mes', yKey: 'total', data: monthRows },
        metadata: { executionTimeMs: 1100, agent: 'mock fixture' },
      }
    }
    return {
      id: crypto.randomUUID(), question: request.question,
      answer: 'Esta é uma resposta demonstrativa. Quando o pipeline estiver conectado, esta pergunta será respondida com base nas colunas e registros do dataset ativo.',
      metadata: { executionTimeMs: 1100, agent: 'mock fixture' },
    }
  }
}
