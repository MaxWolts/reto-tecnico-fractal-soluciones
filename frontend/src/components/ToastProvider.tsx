import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'
import { ToastContext, type ToastApi, type ToastKind } from '../context/ToastContext'
import './Toast.css'

interface ToastItem {
  id: number
  kind: ToastKind
  message: string
}

const DURATION_MS = 4500

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const nextId = useRef(1)

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (kind: ToastKind, message: string) => {
      const id = nextId.current++
      setToasts((current) => [...current, { id, kind, message }])
      window.setTimeout(() => dismiss(id), DURATION_MS)
    },
    [dismiss],
  )

  const api = useMemo<ToastApi>(
    () => ({ success: (m) => push('success', m), error: (m) => push('error', m) }),
    [push],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast--${t.kind}`} role={t.kind === 'error' ? 'alert' : 'status'}>
            <span className="toast__message">{t.message}</span>
            <button type="button" className="toast__close" aria-label="Dismiss" onClick={() => dismiss(t.id)}>
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
