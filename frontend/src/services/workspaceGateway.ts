import type { WorkspaceData, WorkspaceQueryRequest, WorkspaceQueryResponse } from '../contracts/workspace'

interface WorkspaceGateway {
  createWorkspace(name?: string): Promise<WorkspaceData>
  getWorkspace(workspaceId: string): Promise<WorkspaceData>
  addDataset(workspaceId: string, datasetId: string): Promise<WorkspaceData>
  removeDataset(workspaceId: string, datasetId: string): Promise<WorkspaceData>
  queryWorkspace(workspaceId: string, request: WorkspaceQueryRequest): Promise<WorkspaceQueryResponse>
}

class HttpWorkspaceGateway implements WorkspaceGateway {
  async createWorkspace(name: string = ''): Promise<WorkspaceData> {
    const response = await fetch('/api/workspaces', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!response.ok) {
      throw new Error(`Failed to create workspace: ${response.statusText}`)
    }
    return await response.json()
  }

  async getWorkspace(workspaceId: string): Promise<WorkspaceData> {
    const response = await fetch(`/api/workspaces/${workspaceId}`)
    if (!response.ok) {
      throw new Error(`Failed to get workspace: ${response.statusText}`)
    }
    return await response.json()
  }

  async addDataset(workspaceId: string, datasetId: string): Promise<WorkspaceData> {
    const response = await fetch(`/api/workspaces/${workspaceId}/datasets/${datasetId}`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error(`Failed to add dataset: ${response.statusText}`)
    }
    return await response.json()
  }

  async removeDataset(workspaceId: string, datasetId: string): Promise<WorkspaceData> {
    const response = await fetch(`/api/workspaces/${workspaceId}/datasets/${datasetId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to remove dataset: ${response.statusText}`)
    }
    return await response.json()
  }

  async queryWorkspace(
    workspaceId: string,
    request: WorkspaceQueryRequest,
  ): Promise<WorkspaceQueryResponse> {
    const response = await fetch(`/api/workspaces/${workspaceId}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const errorData = await response.json()
      const error = new Error(
        errorData?.error?.message || `Query failed: ${response.statusText}`,
      ) as any
      error.code = errorData?.error?.code
      throw error
    }
    return await response.json()
  }
}

export const workspaceGateway = new HttpWorkspaceGateway()
