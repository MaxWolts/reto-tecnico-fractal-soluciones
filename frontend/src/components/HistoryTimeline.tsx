import type { HistoryEvent, HistoryEventType } from '../types'
import { STATUS_LABEL, formatDateTime, relativeTime, statusModifier } from '../utils'
import './HistoryTimeline.css'

const EVENT_LABEL: Record<HistoryEventType, string> = {
  CREATED: 'Ticket created',
  STATUS_CHANGED: 'Status changed',
  COMMENT: 'Comment',
  ASSIGNED: 'Assignment',
}

const EVENT_ICON: Record<HistoryEventType, string> = {
  CREATED: '+',
  STATUS_CHANGED: '→',
  COMMENT: '"',
  ASSIGNED: '@',
}

function StatusChip({ status }: { status: HistoryEvent['fromStatus'] }) {
  if (!status) return null
  return <span className={`history__chip history__chip--${statusModifier(status)}`}>{STATUS_LABEL[status]}</span>
}

export function HistoryTimeline({ events }: { events: HistoryEvent[] }) {
  if (events.length === 0) return <p className="history__empty">No history yet.</p>
  return (
    <ol className="history">
      {events.map((e) => (
        <li key={e.id} className={`history__item history__item--${e.eventType.toLowerCase().replace('_', '-')}`}>
          <span className="history__icon" aria-hidden="true">
            {EVENT_ICON[e.eventType]}
          </span>
          <div className="history__body">
            <div className="history__head">
              <span className="history__label">{EVENT_LABEL[e.eventType]}</span>
              {(e.fromStatus || e.toStatus) && (
                <span className="history__change">
                  <StatusChip status={e.fromStatus} />
                  {e.fromStatus && e.toStatus && (
                    <span className="history__arrow" aria-label="to">
                      →
                    </span>
                  )}
                  <StatusChip status={e.toStatus} />
                </span>
              )}
            </div>
            {e.comment && <p className="history__comment">{e.comment}</p>}
            <p className="history__meta">
              <span>{e.actor}</span> ·{' '}
              <time dateTime={e.createdAt} title={formatDateTime(e.createdAt)}>
                {relativeTime(e.createdAt)}
              </time>
            </p>
          </div>
        </li>
      ))}
    </ol>
  )
}
