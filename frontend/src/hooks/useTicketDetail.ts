import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { getTicket, getTicketHistory } from '../api/tickets'
import type { HistoryEvent, Ticket } from '../types'

export interface UseTicketDetail {
  ticket: Ticket | null
  history: HistoryEvent[]
  loading: boolean
  error: string | null
  reload: () => Promise<void>
}

/** Loads one ticket with its history. Remount (key=id) to switch tickets. */
export function useTicketDetail(id: number): UseTicketDetail {
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [history, setHistory] = useState<HistoryEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const requestId = useRef(0)

  const reload = useCallback(async () => {
    const current = ++requestId.current
    try {
      const [t, h] = await Promise.all([getTicket(id), getTicketHistory(id)])
      if (current !== requestId.current) return
      setTicket(t)
      setHistory(h)
      setError(null)
    } catch (err) {
      if (current !== requestId.current) return
      setError(err instanceof ApiError ? err.detail : 'Could not load the ticket.')
    } finally {
      if (current === requestId.current) setLoading(false)
    }
  }, [id])

  useEffect(() => {
    // Initial fetch, written as a promise chain so no state is set synchronously.
    const current = ++requestId.current
    Promise.all([getTicket(id), getTicketHistory(id)])
      .then(([t, h]) => {
        if (current !== requestId.current) return
        setTicket(t)
        setHistory(h)
      })
      .catch((err: unknown) => {
        if (current === requestId.current) setError(err instanceof ApiError ? err.detail : 'Could not load the ticket.')
      })
      .finally(() => {
        if (current === requestId.current) setLoading(false)
      })
  }, [id])

  return { ticket, history, loading, error, reload }
}
