import { describe, expect, it } from 'vitest'
import { DataAssistantApiError } from '../../services/http/dataAssistantApiError'
import { getQueryErrorMessage } from './queryErrorMessage'

describe('query error messages', () => {
  it('maps provider and missing dataset errors', () => {
    expect(getQueryErrorMessage(new DataAssistantApiError('ai_provider_unavailable', 'raw', 503))).toContain('não está configurado')
    expect(getQueryErrorMessage(new DataAssistantApiError('dataset_not_found', 'raw', 404))).toContain('não está mais disponível')
  })

  it('maps network failures and hides unknown technical messages', () => {
    expect(getQueryErrorMessage(new DataAssistantApiError('network_error', 'raw', 0))).toContain('conectar')
    expect(getQueryErrorMessage(new DataAssistantApiError('other', 'TypeError: raw stack', 500))).toContain('concluir')
  })
})
