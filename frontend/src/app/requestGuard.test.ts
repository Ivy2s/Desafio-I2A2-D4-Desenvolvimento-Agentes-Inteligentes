import { describe, expect, it } from 'vitest'
import { isCurrentRequest } from './requestGuard'

describe('request guard', () => {
  it('accepts only the current request for the active dataset', () => {
    expect(isCurrentRequest(2, 2, 'dataset-b', 'dataset-b')).toBe(true)
    expect(isCurrentRequest(1, 2, 'dataset-b', 'dataset-b')).toBe(false)
    expect(isCurrentRequest(2, 2, 'dataset-a', 'dataset-b')).toBe(false)
  })
})
