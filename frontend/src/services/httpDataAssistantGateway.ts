import { API_BASE_URL } from '../config/api'
import type { DataAssistantGateway, DatasetSummary, QueryRequest, QueryResponse } from '../contracts/dataAssistant'
import type { ApiDatasetResponse, ApiErrorResponse, ApiHealthResponse, ApiQueryResponse } from './http/apiTypes'
import { toDatasetSummary, toQueryResponse } from './http/dataAssistantApiAdapter'
import { DataAssistantApiError } from './http/dataAssistantApiError'

type FetchLike = typeof fetch

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null
const isApiErrorResponse = (value: unknown): value is ApiErrorResponse => isRecord(value) && isRecord(value.error) && typeof value.error.code === 'string' && typeof value.error.message === 'string'

export class HttpDataAssistantGateway implements DataAssistantGateway {
  private readonly baseUrl: string
  private readonly fetcher: FetchLike

  constructor(baseUrl = API_BASE_URL, fetcher: FetchLike = globalThis.fetch.bind(globalThis)) {
    this.baseUrl = baseUrl.replace(/\/+$/, '')
    this.fetcher = fetcher
  }

  async health(): Promise<ApiHealthResponse> {
    return this.request<ApiHealthResponse>('/api/health')
  }

  async uploadDataset(file: File): Promise<DatasetSummary> {
    const formData = new FormData()
    formData.append('file', file)
    return toDatasetSummary(await this.request<ApiDatasetResponse>('/api/datasets', { method: 'POST', body: formData }))
  }

  async getDataset(datasetId: string): Promise<DatasetSummary> {
    return toDatasetSummary(await this.request<ApiDatasetResponse>(this.datasetPath(datasetId)))
  }

  async queryDataset(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.request<ApiQueryResponse>(`${this.datasetPath(request.datasetId)}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: request.question }),
    })
    return toQueryResponse(response, request.question)
  }

  private datasetPath(datasetId: string) {
    return `/api/datasets/${encodeURIComponent(datasetId)}`
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response
    try {
      response = await this.fetcher(`${this.baseUrl}${path}`, init)
    } catch {
      throw new DataAssistantApiError('network_error', 'Não foi possível conectar à API.', 0)
    }

    const text = await response.text()
    let payload: unknown
    if (text) {
      try {
        payload = JSON.parse(text)
      } catch {
        throw new DataAssistantApiError('invalid_response', 'A API retornou uma resposta inválida.', response.status)
      }
    }

    if (!response.ok) {
      if (isApiErrorResponse(payload)) throw new DataAssistantApiError(payload.error.code, payload.error.message, response.status, payload.error.details)
      throw new DataAssistantApiError('http_error', `A API retornou o status ${response.status}.`, response.status)
    }

    if (!isRecord(payload)) throw new DataAssistantApiError('invalid_response', 'A API retornou uma resposta inválida.', response.status)
    return payload as T
  }
}
