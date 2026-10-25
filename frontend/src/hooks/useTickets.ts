import { useCallback, useEffect, useRef, useState } from 'react'
import { listTickets } from '../api/tickets'
import { ApiError } from '../api/client'
import type { Ticket } from '../types'

export interface UseTickets {
  tickets: Ticket[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useTickets(): UseTickets {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const requestId = useRef(0)

  const load = useCallback(async () => {
    const id = ++requestId.current
    try {
      const data = await listTickets()
      if (id !== requestId.current) return
      setTickets(data)
      setError(null)
    } catch (err) {
      if (id !== requestId.current) return
      setError(err instanceof ApiError ? err.detail : 'Could not load tickets.')
    } finally {
      if (id === requestId.current) setLoading(false)
    }
  }, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    await load()
  }, [load])

  useEffect(() => {
    // Initial load; `loading` already starts as true.
    const id = ++requestId.current
    listTickets()
      .then((data) => {
        if (id === requestId.current) setTickets(data)
      })
      .catch((err: unknown) => {
        if (id === requestId.current) setError(err instanceof ApiError ? err.detail : 'Could not load tickets.')
      })
      .finally(() => {
        if (id === requestId.current) setLoading(false)
      })
  }, [])

  return { tickets, loading, error, refresh }
}
