import type { Role } from '../types'
import { initials } from '../utils'
import './Header.css'

interface HeaderProps {
  userName: string
  role: Role
  onRoleChange: (role: Role) => void
}

const ROLES: Role[] = ['Reporter', 'Operator']

export function Header({ userName, role, onRoleChange }: HeaderProps) {
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
        <span className="header__name">{userName}</span>
        <span className="header__avatar" aria-hidden="true">
          {initials(userName)}
        </span>
      </div>
    </header>
  )
}
