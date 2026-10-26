import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { ToastContext, type ToastApi, type ToastKind } from '../context/ToastContext'
import { CLOSE_MS } from '../hooks/useClosing'
import { XmarkIcon } from './Icons'
import './Toast.css'

interface ToastItem {
  id: number
  kind: ToastKind
  message: string
  closing: boolean
}

/** Success toasts auto-dismiss; error toasts stay until dismissed. */
const DURATION_MS = 4500

interface ToastViewProps {
  toast: ToastItem
  onDismiss: (id: number) => void
}

function ToastView({ toast, onDismiss }: ToastViewProps) {
  const { id, kind, message, closing } = toast
  const [paused, setPaused] = useState(false)
  const remaining = useRef(DURATION_MS)

  useEffect(() => {
    if (kind === 'error' || paused || closing) return
    const startedAt = Date.now()
    const timer = window.setTimeout(() => onDismiss(id), remaining.current)
    return () => {
      window.clearTimeout(timer)
      remaining.current = Math.max(0, remaining.current - (Date.now() - startedAt))
    }
  }, [kind, paused, closing, id, onDismiss])

  return (
    <div
      className={`toast toast--${kind}${closing ? ' toast--closing' : ''}`}
      role={kind === 'error' ? 'alert' : 'status'}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <span className="toast__message">{message}</span>
      <button type="button" className="icon-btn" aria-label="Dismiss" onClick={() => onDismiss(id)}>
        <XmarkIcon />
      </button>
    </div>
  )
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const nextId = useRef(1)

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.map((t) => (t.id === id ? { ...t, closing: true } : t)))
    window.setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), CLOSE_MS)
  }, [])

  const push = useCallback((kind: ToastKind, message: string) => {
    const id = nextId.current++
    setToasts((current) => [...current, { id, kind, message, closing: false }])
  }, [])

  const api = useMemo<ToastApi>(
    () => ({ success: (m) => push('success', m), error: (m) => push('error', m) }),
    [push],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toasts">
        {toasts.map((t) => (
          <ToastView key={t.id} toast={t} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}
