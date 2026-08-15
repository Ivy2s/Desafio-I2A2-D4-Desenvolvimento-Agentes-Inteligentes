import { describe, expect, it } from 'vitest'
import { chartAxisValue, chartTicks, chartTooltipValue, compactNumber, isCurrencyMetric } from './chartFormatting'

describe('chart number formatting', () => {
  it.each([
    [0, '0'], [100, '100'], [1000, '1 mil'], [12500, '12,5 mil'],
    [646200, '646,2 mil'], [1292418.75, '1,29 mi'], [1000000000, '1 bi'],
  ])('formats %s as %s', (value, expected) => expect(compactNumber(value)).toBe(expected))

  it('formats currency only for semantic monetary metrics', () => {
    expect(isCurrencyMetric('valor_total')).toBe(true)
    expect(isCurrencyMetric('quantidade')).toBe(false)
    expect(chartAxisValue(500000, 'valor_total')).toBe('R$ 500 mil')
    expect(chartAxisValue(500000, 'quantidade')).toBe('500 mil')
    expect(chartTooltipValue(1292418.75, 'valor_total')).toBe('R$ 1.292.418,75')
  })
})

describe('chart ticks', () => {
  it('creates a readable zero-based bar scale', () => {
    expect(chartTicks([0, 646200, 1292418.75], 'bar')).toEqual([0, 500000, 1000000, 1500000])
  })

  it('keeps negative values in the domain', () => {
    const ticks = chartTicks([-10, 0, 10], 'bar')
    expect(ticks[0]).toBeLessThan(0)
    expect(ticks.at(-1)).toBeGreaterThan(0)
  })
})
