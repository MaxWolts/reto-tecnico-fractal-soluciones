import { useId, useRef, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { addComment, assignTicket, transitionTicket } from '../api/tickets'
import { useToast } from '../context/ToastContext'
import type { CurrentUser } from '../hooks/useCurrentUser'
import { useModal } from '../hooks/useModal'
import { useTicketDetail } from '../hooks/useTicketDetail'
import type { AllowedTransition, Operator } from '../types'
import { PRIORITY_LABEL, STATUS_LABEL, formatDateTime, statusModifier, transitionLabel } from '../utils'
import { HistoryTimeline } from './HistoryTimeline'
import { TransitionDialog, type TransitionPayload } from './TransitionDialog'
import './TicketDrawer.css'

interface TicketDrawerProps {
  ticketId: number
  user: CurrentUser
  operators: Operator[]
  onClose: () => void
  /** Called after any mutation so the board can refresh. */
  onChanged: () => void
}

const FINAL_STATUSES = ['RESOLVED', 'CANCELLED']

export function TicketDrawer({ ticketId, user, operators, onClose, onChanged }: TicketDrawerProps) {
  const toast = useToast()
  const { ticket, history, loading, error, reload } = useTicketDetail(ticketId)
  const panelRef = useRef<HTMLElement>(null)
  const titleId = useId()
  const onKeyDown = useModal(panelRef, onClose)

  const [pending, setPending] = useState<AllowedTransition | null>(null)
  const [dialogError, setDialogError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [comment, setComment] = useState('')
  const [commenting, setCommenting] = useState(false)
  const [assigning, setAssigning] = useState(false)

  const isOperator = user.role === 'Operator'

  async function refreshAll() {
    await Promise.all([reload(), Promise.resolve(onChanged())])
  }

  /** 409: someone else changed the ticket. Anything else falls through to a toast. */
  function handleCommonError(err: unknown, fallback: string) {
    if (err instanceof ApiError && err.status === 409) {
      toast.error('Ticket was updated by someone else. Reloaded.')
      void refreshAll()
      return
    }
    toast.error(err instanceof ApiError ? err.detail : fallback)
  }

  function openTransition(transition: AllowedTransition) {
    setDialogError(null)
    setPending(transition)
  }

  async function submitTransition(payload: TransitionPayload) {
    if (!ticket) return
    setSubmitting(true)
    setDialogError(null)
    try {
      await transitionTicket(ticket.id, { ...payload, actor: user.name, version: ticket.version })
      setPending(null)
      toast.success(`${ticket.code} moved to ${STATUS_LABEL[payload.toStatus]}`)
      await refreshAll()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setPending(null)
        handleCommonError(err, '')
      } else if (err instanceof ApiError && (err.status === 422 || err.status === 400)) {
        setDialogError(err.detail)
      } else {
        toast.error(err instanceof ApiError ? err.detail : 'Could not update the ticket.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function changeAssignee(value: string) {
    if (!ticket || assigning) return
    const operatorId = value ? Number(value) : null
    setAssigning(true)
    try {
      await assignTicket(ticket.id, operatorId, user.name, ticket.version)
      toast.success(operatorId === null ? `${ticket.code} unassigned` : `${ticket.code} assigned`)
      await refreshAll()
    } catch (err) {
      handleCommonError(err, 'Could not change the assignee.')
    } finally {
      setAssigning(false)
    }
  }

  async function submitComment(event: FormEvent) {
    event.preventDefault()
    const text = comment.trim()
    if (!ticket || !text || commenting) return
    setCommenting(true)
    try {
      await addComment(ticket.id, text, user.name)
      setComment('')
      toast.success('Comment added')
      await refreshAll()
    } catch (err) {
      handleCommonError(err, 'Could not add the comment.')
    } finally {
      setCommenting(false)
    }
  }

  const isFinal = ticket ? FINAL_STATUSES.includes(ticket.status) : false

  return (
    <div className="drawer__backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside
        ref={panelRef}
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onKeyDown={onKeyDown}
      >
        <header className="drawer__header">
          <div className="drawer__heading">
            <div className="drawer__line">
              <span className="drawer__code">{ticket?.code ?? `#${ticketId}`}</span>
              {ticket && (
                <span className={`drawer__chip drawer__chip--${statusModifier(ticket.status)}`}>
                  {STATUS_LABEL[ticket.status]}
                </span>
              )}
            </div>
            <h2 id={titleId} className="drawer__title">
              {ticket?.title ?? (loading ? 'Loading…' : 'Ticket')}
            </h2>
          </div>
          <button type="button" className="drawer__close" aria-label="Close ticket details" onClick={onClose}>
            ×
          </button>
        </header>

        <div className="drawer__scroll">
          {error && (
            <div className="drawer__error" role="alert">
              <span>{error}</span>
              <button type="button" className="drawer__btn" onClick={() => void reload()}>
                Retry
              </button>
            </div>
          )}
          {loading && !ticket && <p className="drawer__muted">Loading ticket…</p>}

          {ticket && (
            <>
              <section aria-label="Details">
                <dl className="drawer__details">
                  <dt>Asset</dt>
                  <dd>{ticket.assetCode}</dd>
                  <dt>Priority</dt>
                  <dd>{PRIORITY_LABEL[ticket.priority]}</dd>
                  <dt>Reporter</dt>
                  <dd>{ticket.reportedBy}</dd>
                  <dt>
                    <label htmlFor={`${titleId}-assignee`}>Assignee</label>
                  </dt>
                  <dd>
                    {isOperator ? (
                      <select
                        id={`${titleId}-assignee`}
                        className="drawer__input drawer__select"
                        value={ticket.assignedOperator?.id ?? ''}
                        disabled={assigning}
                        onChange={(e) => void changeAssignee(e.target.value)}
                      >
                        <option value="">Unassigned</option>
                        {operators.map((o) => (
                          <option key={o.id} value={o.id}>
                            {o.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      (ticket.assignedOperator?.name ?? 'Unassigned')
                    )}
                  </dd>
                  <dt>Created</dt>
                  <dd>{formatDateTime(ticket.createdAt)}</dd>
                  <dt>Updated</dt>
                  <dd>{formatDateTime(ticket.updatedAt)}</dd>
                </dl>
                {ticket.description && <p className="drawer__text">{ticket.description}</p>}
                {ticket.diagnosis && (
                  <div className="drawer__diagnosis">
                    <h3 className="drawer__subtitle">Diagnosis</h3>
                    <p className="drawer__text">{ticket.diagnosis}</p>
                  </div>
                )}
              </section>

              <section aria-label="Actions" className="drawer__section">
                <h3 className="drawer__subtitle">Actions</h3>
                {isFinal || ticket.allowedTransitions.length === 0 ? (
                  <p className="drawer__note">Closed. This ticket is in a final state and cannot change status.</p>
                ) : isOperator ? (
                  <div className="drawer__actions">
                    {ticket.allowedTransitions.map((t) => (
                      <button
                        key={t.toStatus}
                        type="button"
                        className={`drawer__btn${t.toStatus === 'CANCELLED' ? ' drawer__btn--danger' : ' drawer__btn--primary'}`}
                        onClick={() => openTransition(t)}
                      >
                        {transitionLabel(ticket.status, t.toStatus)}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="drawer__note">Read-only: only operators can change the status of a ticket.</p>
                )}
              </section>

              <section aria-label="History" className="drawer__section">
                <h3 className="drawer__subtitle">History</h3>
                <HistoryTimeline events={history} />
                <form className="drawer__comment" onSubmit={(e) => void submitComment(e)}>
                  <label className="drawer__comment-label" htmlFor={`${titleId}-comment`}>
                    Add a comment
                  </label>
                  <textarea
                    id={`${titleId}-comment`}
                    className="drawer__input"
                    rows={3}
                    maxLength={1000}
                    value={comment}
                    disabled={commenting}
                    onChange={(e) => setComment(e.target.value)}
                  />
                  <button
                    type="submit"
                    className="drawer__btn drawer__btn--primary"
                    disabled={commenting || !comment.trim()}
                  >
                    {commenting ? 'Sending…' : 'Comment'}
                  </button>
                </form>
              </section>
            </>
          )}
        </div>
      </aside>

      {ticket && pending && (
        <TransitionDialog
          key={pending.toStatus}
          fromStatus={ticket.status}
          transition={pending}
          serverError={dialogError}
          submitting={submitting}
          onSubmit={(p) => void submitTransition(p)}
          onCancel={() => setPending(null)}
        />
      )}
    </div>
  )
}
