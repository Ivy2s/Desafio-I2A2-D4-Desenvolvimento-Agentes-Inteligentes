import { MockDataAssistantGateway } from '../mocks/mockDataAssistantGateway'
import type { DataAssistantGateway } from '../contracts/dataAssistant'
import { HttpDataAssistantGateway } from './httpDataAssistantGateway'

class UploadHttpQueryMockGateway implements DataAssistantGateway {
  constructor(private readonly uploadGateway: HttpDataAssistantGateway, private readonly queryGateway: MockDataAssistantGateway) {}

  uploadDataset(file: File) {
    return this.uploadGateway.uploadDataset(file)
  }

  getDataset(datasetId: string) {
    return this.uploadGateway.getDataset(datasetId)
  }

  queryDataset(request: Parameters<DataAssistantGateway['queryDataset']>[0]) {
    return this.queryGateway.queryDataset(request)
  }
}

export const dataAssistantGateway: DataAssistantGateway = new UploadHttpQueryMockGateway(new HttpDataAssistantGateway(), new MockDataAssistantGateway())
