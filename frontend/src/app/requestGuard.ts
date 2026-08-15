export function isCurrentRequest(requestId: number, currentRequestId: number, requestDatasetId: string, currentDatasetId: string | undefined) {
  return requestId === currentRequestId && requestDatasetId === currentDatasetId
}
