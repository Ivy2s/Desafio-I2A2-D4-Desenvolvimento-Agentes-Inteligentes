import { MockDataAssistantGateway } from '../mocks/mockDataAssistantGateway'
import type { DataAssistantGateway } from '../contracts/dataAssistant'

export const dataAssistantGateway: DataAssistantGateway = new MockDataAssistantGateway()
