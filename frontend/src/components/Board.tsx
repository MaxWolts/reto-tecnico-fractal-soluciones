import type { Ticket, TicketStatus } from '../types'
import { STATUS_LABEL } from '../utils'
import { TicketCard } from './TicketCard'
import './Board.css'

const COLUMNS: TicketStatus[] = ['PENDING', 'IN_PROGRESS', 'RESOLVED']

interface BoardProps {
  tickets: Ticket[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onTicketClick: (ticket: Ticket) => void
}

export function Board({ tickets, loading, error, onRetry, onTicketClick }: BoardProps) {
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
      <div className="board__columns">
        {COLUMNS.map((status) => {
          const items = tickets.filter((t) => t.status === status)
          return (
            <div key={status} className="board__column">
              <div className="board__column-head">
                <h2 className={`board__chip board__chip--${status.toLowerCase().replace('_', '-')}`}>
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
