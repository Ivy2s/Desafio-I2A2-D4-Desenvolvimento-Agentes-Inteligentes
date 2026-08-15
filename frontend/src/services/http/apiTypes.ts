export interface ApiHealthResponse {
  status: string
  aiConfigured: boolean
}

export interface ApiColumn {
  name: string
  type: string
}

export interface ApiDatasetEntry {
  name: string
  rows: number
  columnCount: number
  columns: ApiColumn[]
}

export interface ApiDatasetResponse {
  datasetId: string
  status: 'ready' | 'processing' | 'error'
  createdAt: string
  summary: { files: number; rows: number; columns: number }
  datasets: ApiDatasetEntry[]
}

export interface ApiQueryRequest {
  question: string
}

export interface ApiCountData {
  type: 'count'
  value: number
}

export interface ApiTableData {
  type: 'table'
  columns: string[]
  rows: Record<string, unknown>[]
  truncated: boolean
  returnedRows: number
}

export type ApiQueryData = ApiCountData | ApiTableData

export interface ApiQueryResponse {
  answer: string
  data: ApiQueryData | null
}

export interface ApiErrorResponse {
  error: { code: string; message: string; details: unknown }
}
