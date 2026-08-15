import { describe, expect, it, vi } from 'vitest'
import { HttpDataAssistantGateway } from './httpDataAssistantGateway'
import { DataAssistantApiError } from './http/dataAssistantApiError'
import { dataAssistantGateway } from './dataAssistantGateway'

const datasetResponse = {
  datasetId: 'abc', status: 'ready', createdAt: '2026-08-14T21:00:00Z',
  summary: { files: 1, rows: 2, columns: 2 },
  datasets: [{ name: 'vendas', rows: 2, columnCount: 2, columns: [{ name: 'a', type: 'string' }, { name: 'b', type: 'number' }] }],
}

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
const gatewayWith = (handler: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) => new HttpDataAssistantGateway('http://api.test/', handler)

describe('HttpDataAssistantGateway', () => {
  it('is the application gateway used for the real upload and query flow', () => {
    expect(dataAssistantGateway).toBeInstanceOf(HttpDataAssistantGateway)
  })

  it('uploads with FormData and adapts the dataset response', async () => {
    const fetcher = vi.fn(async (_input, init) => {
      expect(init?.method).toBe('POST')
      expect(init?.body).toBeInstanceOf(FormData)
      expect((init?.body as FormData).has('file')).toBe(true)
      return response(datasetResponse, 201)
    })
    const result = await gatewayWith(fetcher).uploadDataset(new File(['a,b\n1,2'], 'vendas.csv', { type: 'text/csv' }))
    expect(result).toMatchObject({ id: 'abc', name: 'vendas', csvFiles: ['vendas'], records: 2, columns: 2 })
  })

  it('gets metadata using the dataset path', async () => {
    const fetcher = vi.fn(async (input) => {
      expect(input).toBe('http://api.test/api/datasets/abc')
      return response(datasetResponse)
    })
    await expect(gatewayWith(fetcher).getDataset('abc')).resolves.toMatchObject({ id: 'abc' })
  })

  it.each([
    [{ answer: 'Texto.', data: null }, { answer: 'Texto.', data: null }],
    [{ answer: '565 registros.', data: { type: 'count', value: 565 } }, { data: { type: 'count', value: 565 } }],
    [{ answer: 'Tabela.', data: { type: 'table', columns: ['b', 'a'], rows: [{ a: 1, b: 2 }], truncated: true, returnedRows: 1 } }, { data: { type: 'table', columns: ['b', 'a'], rows: [{ b: 2, a: 1 }], truncated: true, returnedRows: 1 } }],
  ])('adapts query data', async (body, expected) => {
    const fetcher = vi.fn(async (input, init) => {
      expect(input).toBe('http://api.test/api/datasets/abc/query')
      expect(init?.body).toBe(JSON.stringify({ question: 'Pergunta?' }))
      expect(JSON.parse(init?.body as string)).not.toHaveProperty('datasetId')
      return response(body)
    })
    await expect(gatewayWith(fetcher).queryDataset({ datasetId: 'abc', question: 'Pergunta?' })).resolves.toMatchObject(expected)
  })

  it.each([
    [404, 'dataset_not_found'], [413, 'upload_too_large'], [415, 'unsupported_file_type'], [422, 'validation_error'],
    [503, 'ai_provider_unavailable'], [502, 'tool_execution_failed'], [500, 'internal_error'],
  ])('preserves API error details for %s', async (status, code) => {
    const error = await gatewayWith(async () => response({ error: { code, message: 'Mensagem', details: { reason: 'x' } } }, status)).queryDataset({ datasetId: 'abc', question: 'x' }).catch((value) => value)
    expect(error).toBeInstanceOf(DataAssistantApiError)
    expect(error).toMatchObject({ status, code, message: 'Mensagem', details: { reason: 'x' } })
  })

  it('normalizes network, invalid JSON, empty error and invalid success responses', async () => {
    const network = await gatewayWith(async () => { throw new Error('offline') }).queryDataset({ datasetId: 'abc', question: 'x' }).catch((value) => value)
    const invalidJson = await gatewayWith(async () => new Response('not json', { status: 200 })).queryDataset({ datasetId: 'abc', question: 'x' }).catch((value) => value)
    const emptyError = await gatewayWith(async () => new Response('', { status: 500 })).queryDataset({ datasetId: 'abc', question: 'x' }).catch((value) => value)
    const invalidSuccess = await gatewayWith(async () => response({ foo: 'bar' })).queryDataset({ datasetId: 'abc', question: 'x' }).catch((value) => value)
    expect(network).toMatchObject({ code: 'network_error', status: 0 })
    expect(invalidJson).toMatchObject({ code: 'invalid_response', status: 200 })
    expect(emptyError).toMatchObject({ code: 'http_error', status: 500 })
    expect(invalidSuccess).toMatchObject({ code: 'invalid_response', status: 200 })
  })
})
