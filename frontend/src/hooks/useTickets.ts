import { useCallback, useEffect, useRef, useState } from 'react'
import { listTickets } from '../api/tickets'
import { ApiError } from '../api/client'
import type { Ticket, TicketFilters } from '../types'

export interface UseTickets {
  tickets: Ticket[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useTickets(filters: TicketFilters): UseTickets {
  const [tickets, setTickets] = useState<Ticket[]>([])
  // The filters object the current `tickets` were loaded for; loading = they differ.
  const [loadedFor, setLoadedFor] = useState<TicketFilters | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const requestId = useRef(0)
  const filtersRef = useRef(filters)
  useEffect(() => {
    filtersRef.current = filters
  })

  const run = useCallback((target: TicketFilters) => {
    const id = ++requestId.current
    return listTickets(target)
      .then((data) => {
        if (id !== requestId.current) return
        setTickets(data)
        setError(null)
      })
      .catch((err: unknown) => {
        if (id === requestId.current) setError(err instanceof ApiError ? err.detail : 'Could not load tickets.')
      })
      .finally(() => {
        if (id === requestId.current) {
          setLoadedFor(target)
          setRefreshing(false)
        }
      })
  }, [])

  const refresh = useCallback(async () => {
    setRefreshing(true)
    await run(filtersRef.current)
  }, [run])

  useEffect(() => {
    void run(filters)
  }, [filters, run])

  return { tickets, loading: refreshing || loadedFor !== filters, error, refresh }
}
