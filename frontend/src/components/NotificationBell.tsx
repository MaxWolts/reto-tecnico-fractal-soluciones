import { useEffect, useId, useRef, useState } from 'react'
import { useNotifications } from '../hooks/useNotifications'
import type { Notification } from '../types'
import { STATUS_LABEL, formatDateTime, relativeTime } from '../utils'
import './NotificationBell.css'

interface NotificationBellProps {
  onOpenTicket: (ticketId: number) => void
}

function describe(n: Notification): string {
  const code = `#${n.ticketId}`
  if (n.toStatus) {
    const to = STATUS_LABEL[n.toStatus]
    return n.fromStatus ? `${code} ${STATUS_LABEL[n.fromStatus]} → ${to} by ${n.actor}` : `${code} ${to} by ${n.actor}`
  }
  return `${code} assignment changed by ${n.actor}`
}

export function NotificationBell({ onOpenTicket }: NotificationBellProps) {
  const { items, markAllRead } = useNotifications()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const panelId = useId()

  useEffect(() => {
    if (!open) return
    const onPointer = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        buttonRef.current?.focus()
      }
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="bell" ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className="bell__button"
        aria-haspopup="true"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={items.length > 0 ? `Notifications, ${items.length} unread` : 'Notifications'}
        onClick={() => setOpen((v) => !v)}
      >
        <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.7 21a2 2 0 0 1-3.4 0" />
        </svg>
        {items.length > 0 && (
          <span className="bell__badge" aria-hidden="true">
            {items.length}
          </span>
        )}
      </button>
      {open && (
        <div id={panelId} className="bell__panel" role="region" aria-label="Notifications">
          <div className="bell__head">
            <strong>Notifications</strong>
            <button type="button" className="bell__mark" disabled={items.length === 0} onClick={markAllRead}>
              Mark all read
            </button>
          </div>
          {items.length === 0 ? (
            <p className="bell__empty">No new notifications.</p>
          ) : (
            <ul className="bell__list">
              {items.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    className="bell__item"
                    title={n.ticketTitle}
                    onClick={() => {
                      setOpen(false)
                      onOpenTicket(n.ticketId)
                    }}
                  >
                    <span className="bell__text">{describe(n)}</span>
                    <time className="bell__time" dateTime={n.createdAt} title={formatDateTime(n.createdAt)}>
                      {relativeTime(n.createdAt)}
                    </time>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
