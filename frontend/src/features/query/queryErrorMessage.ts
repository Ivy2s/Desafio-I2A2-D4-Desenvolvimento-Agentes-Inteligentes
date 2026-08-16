import { DataAssistantApiError } from '../../services/http/dataAssistantApiError'

export function getQueryCooldownSeconds(error: unknown) {
  if (!(error instanceof DataAssistantApiError)) return 0
  if (!['provider_rate_limit', 'provider_quota_exhausted'].includes(error.code)) return 0
  const details = error.details
  if (typeof details !== 'object' || details === null) return 0
  const seconds = (details as { retry_after_seconds?: unknown }).retry_after_seconds
  return typeof seconds === 'number' && Number.isFinite(seconds) ? Math.max(1, Math.round(seconds)) : 0
}

export function getQueryErrorMessage(error: unknown) {
  if (!(error instanceof DataAssistantApiError)) return 'Não foi possível concluir a análise.'
  if (error.code === 'ai_provider_unavailable') return 'O serviço de análise por IA não está configurado no backend.'
  if (error.code === 'provider_rate_limit') return 'Limite temporário do provedor. O serviço de IA atingiu o limite de uso por minuto.'
  if (error.code === 'provider_quota_exhausted') return 'A cota do provedor de IA foi esgotada. Tente novamente quando a cota for renovada.'
  if (error.code === 'provider_unavailable') return 'O provedor de IA está temporariamente indisponível. Tente novamente mais tarde.'
  if (error.code === 'dataset_not_found') return 'Este dataset não está mais disponível no servidor. Envie o arquivo novamente.'
  if (error.code === 'agent_timeout') return 'A análise demorou mais que o esperado. Tente novamente.'
  if (error.code === 'agent_iteration_limit') return 'Não foi possível concluir a análise. Tente reformular a pergunta.'
  if (error.code === 'query_invalid') return 'A consulta não pôde ser executada com os dados disponíveis. Tente reformular a pergunta.'
  if (['unknown_tool', 'tool_execution_failed', 'query_execution_error'].includes(error.code)) return 'Ocorreu um erro ao analisar os dados. Tente novamente.'
  if (error.code === 'network_error') return 'Não foi possível conectar ao servidor. Tente novamente.'
  if (error.code === 'validation_error') return 'A pergunta não pôde ser validada. Tente reformulá-la.'
  if (error.code === 'http_error') return 'O servidor não conseguiu concluir a consulta. Tente novamente.'
  if (error.code === 'invalid_response') return 'O servidor retornou uma resposta inválida. Tente novamente.'
  return 'Não foi possível concluir a análise. Tente novamente.'
}
