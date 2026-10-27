import type { CSSProperties } from 'react'
import type { Ticket, TicketStatus } from '../types'
import { STATUS_LABEL, statusModifier } from '../utils'
import { TicketCard } from './TicketCard'
import './Board.css'

const BASE_COLUMNS: TicketStatus[] = ['PENDING', 'IN_PROGRESS', 'RESOLVED']

interface BoardProps {
  tickets: Ticket[]
  loading: boolean
  error: string | null
  /** Status filter currently applied, if any. */
  statusFilter?: TicketStatus
  onRetry: () => void
  onTicketClick: (ticket: Ticket) => void
}

export function Board({ tickets, loading, error, statusFilter, onRetry, onTicketClick }: BoardProps) {
  // The Cancelled column only appears when it has tickets or the filter selects it.
  const showCancelled = statusFilter === 'CANCELLED' || tickets.some((t) => t.status === 'CANCELLED')
  const columns = showCancelled ? [...BASE_COLUMNS, 'CANCELLED' as const] : BASE_COLUMNS
  const showSkeleton = loading && tickets.length === 0
  return (
    <section className="board" aria-label="Ticket board" aria-busy={loading}>
      {error && (
        <div className="board__error" role="alert">
          <span>{error}</span>
          <button type="button" className="board__retry" onClick={onRetry}>
            Retry
          </button>
        </div>
      )}
      <div className={`board__columns${columns.length > 3 ? ' board__columns--wide' : ''}`} style={{ '--columns': columns.length } as CSSProperties}>
        {columns.map((status) => {
          const items = tickets.filter((t) => t.status === status)
          return (
            <div key={status} className="board__column">
              <div className="board__column-head">
                <h2 className={`board__chip board__chip--${statusModifier(status)}`}>
                  {STATUS_LABEL[status]}
                </h2>
                <span className="board__count" aria-label={`${items.length} tickets`}>
                  {showSkeleton ? '–' : items.length}
                </span>
              </div>
              <div className="board__list">
                {showSkeleton &&
                  [0, 1].map((i) => <div key={i} className="board__skeleton" aria-hidden="true" />)}
                {!showSkeleton &&
                  items.map((t) => <TicketCard key={t.id} ticket={t} onClick={onTicketClick} />)}
                {!showSkeleton && items.length === 0 && !error && (
                  <p className="board__empty">No tickets here yet</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
