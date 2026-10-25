import { useCallback, useState } from 'react'
import type { Role } from '../types'

const STORAGE_KEY = 'fractal.currentUser'

export interface CurrentUser {
  name: string
  role: Role
}

const DEFAULT_USER: CurrentUser = { name: 'Operator Demo', role: 'Operator' }

function load(): CurrentUser {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_USER
    const parsed = JSON.parse(raw) as Partial<CurrentUser>
    if (typeof parsed.name === 'string' && parsed.name.trim() && (parsed.role === 'Reporter' || parsed.role === 'Operator')) {
      return { name: parsed.name, role: parsed.role }
    }
  } catch {
    // storage unavailable or corrupt: fall back to default
  }
  return DEFAULT_USER
}

export function useCurrentUser() {
  const [user, setUser] = useState<CurrentUser>(load)

  const setRole = useCallback((role: Role) => {
    setUser((current) => {
      const next = { ...current, role }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        // ignore
      }
      return next
    })
  }, [])

  const setName = useCallback((name: string) => {
    const trimmed = name.trim()
    if (!trimmed) return
    setUser((current) => {
      const next = { ...current, name: trimmed }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        // ignore
      }
      return next
    })
  }, [])

  return { user, setRole, setName }
}
