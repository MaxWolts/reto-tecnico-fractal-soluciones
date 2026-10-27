import { useCallback, useEffect, useState } from 'react'
import { isValidDate } from '../dates'
import { PRIORITIES, STATUSES, type TicketFilters } from '../types'

function fromQuery(search: string): TicketFilters {
  const params = new URLSearchParams(search)
  const filters: TicketFilters = {}
  const status = params.get('status')
  const priority = params.get('priority')
  const operatorId = Number(params.get('operatorId'))
  const from = params.get('from')
  const to = params.get('to')
  const q = params.get('q')?.trim()
  if (status && (STATUSES as string[]).includes(status)) filters.status = status as TicketFilters['status']
  if (priority && (PRIORITIES as string[]).includes(priority)) filters.priority = priority as TicketFilters['priority']
  if (Number.isInteger(operatorId) && operatorId > 0) filters.operatorId = operatorId
  if (from && isValidDate(from)) filters.from = from
  if (to && isValidDate(to)) filters.to = to
  if (q) filters.q = q
  return filters
}

function toQuery(filters: TicketFilters): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  const text = params.toString()
  return text ? `?${text}` : ''
}

/** Board filters, mirrored in the URL query string so a view can be shared. */
export function useFilters() {
  const [filters, setFilters] = useState<TicketFilters>(() => fromQuery(window.location.search))

  useEffect(() => {
    const url = `${window.location.pathname}${toQuery(filters)}${window.location.hash}`
    window.history.replaceState(null, '', url)
  }, [filters])

  const update = useCallback((patch: Partial<TicketFilters>) => {
    setFilters((current) => {
      const next: TicketFilters = { ...current, ...patch }
      for (const key of Object.keys(next) as (keyof TicketFilters)[]) {
        if (next[key] === undefined || next[key] === '') delete next[key]
      }
      return next
    })
  }, [])

  const clear = useCallback(() => setFilters({}), [])

  return { filters, update, clear }
}
