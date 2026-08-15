import { DataAssistantApiError } from '../../services/http/dataAssistantApiError'

export function getQueryErrorMessage(error: unknown) {
  if (!(error instanceof DataAssistantApiError)) return error instanceof Error ? error.message : 'Não foi possível concluir a análise.'
  if (error.code === 'ai_provider_unavailable') return 'O serviço de análise por IA não está configurado no backend.'
  if (error.code === 'dataset_not_found') return 'Este dataset não está mais disponível no servidor. Envie o arquivo novamente.'
  if (error.code === 'agent_timeout') return 'A análise demorou mais que o esperado. Tente novamente.'
  if (error.code === 'agent_iteration_limit') return 'Não foi possível concluir a análise. Tente reformular a pergunta.'
  if (['unknown_tool', 'tool_execution_failed', 'query_execution_error'].includes(error.code)) return 'Ocorreu um erro ao analisar os dados. Tente novamente.'
  if (error.code === 'network_error') return 'Não foi possível conectar ao servidor. Tente novamente.'
  if (error.code === 'invalid_response') return 'O servidor retornou uma resposta inválida. Tente novamente.'
  return error.message
}
