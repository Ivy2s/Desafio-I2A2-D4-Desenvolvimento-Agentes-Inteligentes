import { describe, expect, it } from 'vitest'
import { DataAssistantApiError } from '../../services/http/dataAssistantApiError'
import { getQueryCooldownSeconds, getQueryErrorMessage } from './queryErrorMessage'

describe('query error messages', () => {
  it('maps provider and missing dataset errors', () => {
    expect(getQueryErrorMessage(new DataAssistantApiError('ai_provider_unavailable', 'raw', 503))).toContain('não está configurado')
    expect(getQueryErrorMessage(new DataAssistantApiError('dataset_not_found', 'raw', 404))).toContain('não está mais disponível')
  })

  it('maps network failures and hides unknown technical messages', () => {
    expect(getQueryErrorMessage(new DataAssistantApiError('network_error', 'raw', 0))).toContain('conectar')
    expect(getQueryErrorMessage(new DataAssistantApiError('other', 'TypeError: raw stack', 500))).toContain('concluir')
  })

  it('shows the provider wait time for rate limits', () => {
    expect(getQueryErrorMessage(new DataAssistantApiError('provider_rate_limit', 'raw', 429))).toContain('Limite temporário')
    expect(getQueryCooldownSeconds(new DataAssistantApiError('provider_rate_limit', 'raw', 429, { retry_after_seconds: 7 }))).toBe(7)
    expect(getQueryCooldownSeconds(new DataAssistantApiError('provider_rate_limit', 'raw', 429))).toBe(0)
  })

  it('keeps provider quota errors distinct from generic analysis errors', () => {
    expect(getQueryErrorMessage(new DataAssistantApiError('provider_quota_exhausted', 'raw', 429))).toContain('cota')
    expect(getQueryErrorMessage(new DataAssistantApiError('query_invalid', 'raw', 422))).toContain('dados disponíveis')
  })
})
