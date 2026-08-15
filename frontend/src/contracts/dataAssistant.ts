export type UploadState = 'idle' | 'drag-active' | 'validating' | 'selected' | 'uploading' | 'processing' | 'ready' | 'invalid-file' | 'error'

export interface DatasetFile {
  name: string
  size: number
  type: string
}

export interface DatasetSummary {
  id: string
  name: string
  csvFiles: string[]
  records: number
  columns: number
  status: 'ready' | 'processing' | 'error'
}

export interface QueryRequest {
  datasetId: string
  question: string
}

export interface CountData { type: 'count'; value: number }

export interface TableData {
  type: 'table'
  columns: string[]
  rows: Record<string, unknown>[]
  truncated: boolean
  returnedRows: number
}

export type QueryData = CountData | TableData

export interface QueryResponse {
  id: string
  question: string
  answer: string
  data: QueryData | null
  metadata?: { executionTimeMs?: number; agent?: string }
}

export interface DataAssistantGateway {
  uploadDataset(file: File): Promise<DatasetSummary>
  getDataset(datasetId: string): Promise<DatasetSummary>
  queryDataset(request: QueryRequest): Promise<QueryResponse>
}
