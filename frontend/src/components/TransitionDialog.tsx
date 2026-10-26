import { useId, useRef, useState, type FormEvent } from 'react'
import { createPortal } from 'react-dom'
import { useBodyScrollLock } from '../hooks/useBodyScrollLock'
import { useClosing } from '../hooks/useClosing'
import { useModal } from '../hooks/useModal'
import type { AllowedTransition, TicketStatus } from '../types'
import { STATUS_LABEL, transitionLabel } from '../utils'
import './TransitionDialog.css'

export interface TransitionPayload {
  toStatus: TicketStatus
  diagnosis?: string
  comment?: string
}

interface TransitionDialogProps {
  fromStatus: TicketStatus
  transition: AllowedTransition
  /** Business error returned by the server, shown inline. */
  serverError: string | null
  submitting: boolean
  onSubmit: (payload: TransitionPayload) => void
  onCancel: () => void
}

export function TransitionDialog({
  fromStatus,
  transition,
  serverError,
  submitting,
  onSubmit,
  onCancel,
}: TransitionDialogProps) {
  const ref = useRef<HTMLDivElement>(null)
  const titleId = useId()
  const [closing, requestClose] = useClosing(onCancel)
  const onKeyDown = useModal(ref, requestClose)
  useBodyScrollLock()
  const isCancel = transition.toStatus === 'CANCELLED'
  const actionLabel = transitionLabel(fromStatus, transition.toStatus)
  const [diagnosis, setDiagnosis] = useState('')
  const [comment, setComment] = useState('')
  const [errors, setErrors] = useState<{ diagnosis?: string; comment?: string }>({})

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (submitting) return
    const found: typeof errors = {}
    if (transition.requiresDiagnosis && !diagnosis.trim()) found.diagnosis = 'Diagnosis is required.'
    if (transition.requiresComment && !comment.trim()) found.comment = 'A comment is required.'
    setErrors(found)
    if (Object.keys(found).length > 0) return
    onSubmit({
      toStatus: transition.toStatus,
      diagnosis: diagnosis.trim() || undefined,
      comment: comment.trim() || undefined,
    })
  }

  return createPortal(
    <div className={`dialog__backdrop${closing ? ' dialog__backdrop--closing' : ''}`}>
      <div
        ref={ref}
        className={`dialog${closing ? ' dialog--closing' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onKeyDown={onKeyDown}
      >
        <form onSubmit={handleSubmit} noValidate>
          <h2 id={titleId} className="dialog__title">
            {actionLabel}
          </h2>
          <p className="dialog__sub">
            {STATUS_LABEL[fromStatus]} → {STATUS_LABEL[transition.toStatus]}
          </p>
          {transition.requiresDiagnosis && (
            <label className="dialog__field">
              <span className="dialog__label">Diagnosis (required)</span>
              <textarea
                className="dialog__input"
                data-autofocus
                rows={4}
                maxLength={1000}
                value={diagnosis}
                aria-invalid={errors.diagnosis ? true : undefined}
                onChange={(e) => setDiagnosis(e.target.value)}
              />
              {errors.diagnosis && (
                <span className="dialog__error" role="alert">
                  {errors.diagnosis}
                </span>
              )}
            </label>
          )}
          <label className="dialog__field">
            <span className="dialog__label">
              {transition.requiresComment ? 'Comment (required)' : 'Comment (optional)'}
            </span>
            <textarea
              className="dialog__input"
              data-autofocus={transition.requiresDiagnosis ? undefined : true}
              rows={3}
              maxLength={1000}
              value={comment}
              aria-invalid={errors.comment ? true : undefined}
              onChange={(e) => setComment(e.target.value)}
            />
            {errors.comment && (
              <span className="dialog__error" role="alert">
                {errors.comment}
              </span>
            )}
          </label>
          {serverError && (
            <p className="dialog__error dialog__error--server" role="alert">
              {serverError}
            </p>
          )}
          <div className="dialog__actions">
            <button type="button" className="dialog__btn" onClick={requestClose} disabled={submitting}>
              {isCancel ? 'Keep ticket' : 'Back'}
            </button>
            <button
              type="submit"
              className={`dialog__btn ${isCancel ? 'dialog__btn--danger' : 'dialog__btn--primary'}`}
              disabled={submitting}
            >
              {submitting ? 'Saving…' : actionLabel}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  )
}
