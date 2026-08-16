// Contrato com a API de workspace
import type { QueryData } from './dataAssistant'

export interface WorkspaceDataset {
  datasetId: string
  name: string
  fileNames: string[]
  rows: number
  columns: number
}

export interface WorkspaceSummary {
  files: number
  rows: number
  columns: number
}

export interface WorkspaceData {
  workspaceId: string
  name: string
  createdAt: string
  datasets: WorkspaceDataset[]
  summary: WorkspaceSummary
}

export interface WorkspaceQueryRequest {
  question: string
}

export interface WorkspaceQueryResponse {
  answer: string
  data: QueryData | null
}
