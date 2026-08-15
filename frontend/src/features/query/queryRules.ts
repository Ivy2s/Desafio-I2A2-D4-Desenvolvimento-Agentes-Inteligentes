export const MAX_QUERY_LENGTH = 4000

export function normalizeQuestion(value: string) {
  return value.trim().slice(0, MAX_QUERY_LENGTH)
}

export function canSubmitQuery(datasetId: string | undefined, question: string, querying: boolean) {
  return Boolean(datasetId && normalizeQuestion(question) && !querying)
}
