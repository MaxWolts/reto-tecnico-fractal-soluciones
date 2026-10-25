import type { Ticket } from '../types'
import { PRIORITY_LABEL, initials, relativeTime } from '../utils'
import './TicketCard.css'

interface TicketCardProps {
  ticket: Ticket
  onClick: (ticket: Ticket) => void
}

export function TicketCard({ ticket, onClick }: TicketCardProps) {
  const assignee = ticket.assignedOperator
  return (
    <button type="button" className="ticket-card" onClick={() => onClick(ticket)}>
      <span className="ticket-card__top">
        <span className="ticket-card__code">{ticket.code}</span>
        <span className="ticket-card__time">{relativeTime(ticket.createdAt)}</span>
      </span>
      <span className="ticket-card__title">{ticket.title}</span>
      <span className="ticket-card__bottom">
        <span className="ticket-card__asset">{ticket.assetCode}</span>
        <span className="ticket-card__priority">
          <span className={`ticket-card__dot ticket-card__dot--${ticket.priority.toLowerCase()}`} aria-hidden="true" />
          {PRIORITY_LABEL[ticket.priority]}
        </span>
        {assignee && (
          <span className="ticket-card__assignee" title={`Assigned to ${assignee.name}`}>
            <span className="ticket-card__initials" aria-hidden="true">
              {initials(assignee.name)}
            </span>
            <span className="ticket-card__sr">Assigned to {assignee.name}</span>
          </span>
        )}
      </span>
    </button>
  )
}
