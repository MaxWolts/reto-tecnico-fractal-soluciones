import { useState } from 'react'
import type { Role } from '../types'
import { initials } from '../utils'
import { NotificationBell } from './NotificationBell'
import './Header.css'

interface HeaderProps {
  userName: string
  role: Role
  onRoleChange: (role: Role) => void
  onNameChange: (name: string) => void
  onOpenTicket: (ticketId: number) => void
}

const ROLES: Role[] = ['Reporter', 'Operator']

export function Header({ userName, role, onRoleChange, onNameChange, onOpenTicket }: HeaderProps) {
  const [draft, setDraft] = useState(userName)
  const [prevName, setPrevName] = useState(userName)
  if (prevName !== userName) {
    setPrevName(userName)
    setDraft(userName)
  }

  function commit() {
    const trimmed = draft.trim()
    if (trimmed && trimmed !== userName) onNameChange(trimmed)
    else setDraft(userName)
  }

  return (
    <header className="header">
      <div className="header__brand">
        <span className="header__logo" aria-label="Fractal">
          FRACTAL
        </span>
        <span className="header__divider" aria-hidden="true" />
        <h1 className="header__title">Maintenance · Tickets</h1>
      </div>
      <div className="header__user">
        <NotificationBell onOpenTicket={onOpenTicket} />
        <div className="header__roles" role="group" aria-label="Role">
          {ROLES.map((r) => (
            <button
              key={r}
              type="button"
              className={`header__role${r === role ? ' header__role--active' : ''}`}
              aria-pressed={r === role}
              onClick={() => onRoleChange(r)}
            >
              {r}
            </button>
          ))}
        </div>
        <input
          className="header__name"
          aria-label="Your name (used as actor in the history)"
          value={draft}
          maxLength={100}
          size={Math.max(8, Math.min(draft.length, 24))}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.currentTarget.blur()
            if (e.key === 'Escape') setDraft(userName)
          }}
        />
        <span className="header__avatar" aria-hidden="true">
          {initials(userName)}
        </span>
      </div>
    </header>
  )
}
