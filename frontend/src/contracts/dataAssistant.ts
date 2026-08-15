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

export type ChartType = 'bar' | 'line' | 'pie'

export interface QueryResponse {
  id: string
  question: string
  answer: string
  count?: number
  table?: { columns: string[]; rows: Record<string, unknown>[]; truncated?: boolean; returnedRows?: number }
  chart?: { type: ChartType; title?: string; xKey: string; yKey: string; data: Record<string, unknown>[] }
  metadata?: { executionTimeMs?: number; agent?: string }
}

export interface DataAssistantGateway {
  uploadDataset(file: File): Promise<DatasetSummary>
  getDataset(datasetId: string): Promise<DatasetSummary>
  queryDataset(request: QueryRequest): Promise<QueryResponse>
}
