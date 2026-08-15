import type { DatasetSummary, QueryResponse } from '../../contracts/dataAssistant'
import type { ApiDatasetResponse, ApiQueryResponse } from './apiTypes'
import { DataAssistantApiError } from './dataAssistantApiError'

const invalidResponse = () => new DataAssistantApiError('invalid_response', 'A API retornou uma resposta inválida.', 200)

function assertDatasetResponse(response: ApiDatasetResponse): asserts response is ApiDatasetResponse {
  if (typeof response.datasetId !== 'string' || !response.summary || typeof response.summary.rows !== 'number' || typeof response.summary.columns !== 'number' || !Array.isArray(response.datasets)) throw invalidResponse()
}

function assertQueryResponse(response: ApiQueryResponse): asserts response is ApiQueryResponse {
  if (typeof response.answer !== 'string' || (response.data !== null && (!response.data || typeof response.data !== 'object' || !('type' in response.data) || response.data.type !== 'count' && response.data.type !== 'table'))) throw invalidResponse()
  if (response.data?.type === 'count' && typeof response.data.value !== 'number') throw invalidResponse()
  if (response.data?.type === 'table' && (!Array.isArray(response.data.columns) || !Array.isArray(response.data.rows) || typeof response.data.truncated !== 'boolean' || typeof response.data.returnedRows !== 'number')) throw invalidResponse()
}

export function toDatasetSummary(response: ApiDatasetResponse): DatasetSummary {
  assertDatasetResponse(response)
  const firstDataset = response.datasets[0]
  return {
    id: response.datasetId,
    name: firstDataset?.name ?? 'Dataset',
    csvFiles: response.datasets.map((dataset) => dataset.name),
    records: response.summary.rows,
    columns: response.summary.columns,
    status: response.status,
  }
}

export function toQueryResponse(response: ApiQueryResponse, question: string): QueryResponse {
  assertQueryResponse(response)
  if (response.data === null) {
    return { id: crypto.randomUUID(), question, answer: response.answer, data: null }
  }

  if (response.data.type === 'count') {
    return { id: crypto.randomUUID(), question, answer: response.answer, data: response.data }
  }

  const tableData = response.data
  return {
    id: crypto.randomUUID(),
    question,
    answer: response.answer,
    data: {
      type: 'table',
      columns: tableData.columns,
      rows: tableData.rows.map((row) => Object.fromEntries(tableData.columns.map((column) => [column, row[column]]))),
      truncated: tableData.truncated,
      returnedRows: tableData.returnedRows,
    },
  }
}
