import type { DataAssistantGateway } from '../contracts/dataAssistant'
import { HttpDataAssistantGateway } from './httpDataAssistantGateway'

export const dataAssistantGateway: DataAssistantGateway = new HttpDataAssistantGateway()
