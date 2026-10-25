import { useCallback, useEffect, useRef, useState } from 'react'
import { listNotifications } from '../api/tickets'
import type { Notification } from '../types'

const STORAGE_KEY = 'fractal.notificationsLastSeen'
const POLL_MS = 15_000

function loadLastSeen(): string {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) return stored
  } catch {
    // storage unavailable: fall through to "now"
  }
  return new Date().toISOString()
}

function saveLastSeen(value: string) {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // ignore
  }
}

/**
 * Notifications are simulated: the backend derives them from ticket history
 * events (status changes and assignments), there is no push channel. We poll
 * every 15 s (paused while the tab is hidden) for events newer than the last
 * time the user marked everything as read.
 */
export function useNotifications() {
  const [lastSeen, setLastSeen] = useState<string>(loadLastSeen)
  const [items, setItems] = useState<Notification[]>([])
  const lastSeenRef = useRef(lastSeen)
  useEffect(() => {
    lastSeenRef.current = lastSeen
  })

  const poll = useCallback(async () => {
    const since = lastSeenRef.current
    try {
      const data = await listNotifications(since)
      // Ignore a response that raced with "mark all read".
      if (since === lastSeenRef.current) setItems(data)
    } catch {
      // Polling failures are silent; the next tick retries.
    }
  }, [])

  useEffect(() => {
    let timer: number | undefined
    const start = () => {
      void poll()
      timer = window.setInterval(() => void poll(), POLL_MS)
    }
    const stop = () => {
      window.clearInterval(timer)
      timer = undefined
    }
    const onVisibility = () => {
      stop()
      if (!document.hidden) start()
    }
    if (!document.hidden) start()
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      stop()
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [poll, lastSeen])

  const markAllRead = useCallback(() => {
    // Prefer the newest event time over the client clock to avoid skew.
    const newest = items.reduce((max, n) => (n.createdAt > max ? n.createdAt : max), '')
    const next = newest || new Date().toISOString()
    saveLastSeen(next)
    lastSeenRef.current = next
    setLastSeen(next)
    setItems([])
  }, [items])

  return { items, markAllRead }
}
