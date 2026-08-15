import { describe, expect, it } from 'vitest'
import { canSubmitQuery, normalizeQuestion } from './queryRules'

describe('query rules', () => {
  it.each([
    [undefined, 'pergunta', false, false],
    ['dataset-id', '   ', false, false],
    ['dataset-id', 'pergunta', true, false],
    ['dataset-id', 'pergunta', false, true],
  ])('allows only valid active submissions', (datasetId, question, querying, expected) => {
    expect(canSubmitQuery(datasetId, question, querying)).toBe(expected)
  })

  it('trims and caps questions at the backend contract limit', () => {
    expect(normalizeQuestion('  pergunta  ')).toBe('pergunta')
    expect(normalizeQuestion('x'.repeat(5000))).toHaveLength(4000)
  })
})
