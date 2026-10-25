import { useState, type FormEvent } from 'react'
import { createTicket } from '../api/tickets'
import { ApiError } from '../api/client'
import { useToast } from '../context/ToastContext'
import { PRIORITIES, type Priority, type Ticket } from '../types'
import { PRIORITY_LABEL } from '../utils'
import { validate, type Errors, type Field } from './validation'
import './CreateTicketForm.css'

interface CreateTicketFormProps {
  currentUser: string
  onCreated: (ticket: Ticket) => void
}

export function CreateTicketForm({ currentUser, onCreated }: CreateTicketFormProps) {
  const toast = useToast()
  const [title, setTitle] = useState('')
  const [assetCode, setAssetCode] = useState('')
  const [priority, setPriority] = useState<Priority>('MEDIUM')
  const [description, setDescription] = useState('')
  const [reportedBy, setReportedBy] = useState(currentUser)
  const [prevUser, setPrevUser] = useState(currentUser)
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Keep the prefilled reporter in sync when the current user changes.
  if (prevUser !== currentUser) {
    setPrevUser(currentUser)
    setReportedBy(currentUser)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (submitting) return
    const found = validate({ title, assetCode, description, reportedBy })
    setErrors(found)
    setFormError(null)
    if (Object.keys(found).length > 0) return

    setSubmitting(true)
    try {
      const ticket = await createTicket({
        title: title.trim(),
        assetCode: assetCode.trim(),
        priority,
        description: description.trim() || undefined,
        reportedBy: reportedBy.trim(),
      })
      setTitle('')
      setAssetCode('')
      setDescription('')
      setPriority('MEDIUM')
      setErrors({})
      toast.success(`Ticket ${ticket.code} created`)
      onCreated(ticket)
    } catch (err) {
      if (err instanceof ApiError) {
        const mapped: Errors = {}
        for (const e of err.errors) {
          const key = e.field.split('.').pop() as Field
          if (['title', 'assetCode', 'description', 'reportedBy'].includes(key)) mapped[key] = e.message
        }
        setErrors(mapped)
        setFormError(Object.keys(mapped).length === 0 ? err.detail : null)
        toast.error(err.detail)
      } else {
        toast.error('Could not create the ticket.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  function fieldProps(field: Field) {
    return {
      'aria-invalid': errors[field] ? true : undefined,
      'aria-describedby': errors[field] ? `ticket-${field}-error` : undefined,
    }
  }

  function renderError(field: Field) {
    return errors[field] ? (
      <span id={`ticket-${field}-error`} className="create-form__error" role="alert">
        {errors[field]}
      </span>
    ) : null
  }

  return (
    <form className="create-form" onSubmit={handleSubmit} noValidate>
      <h2 className="create-form__title">New ticket</h2>
      <fieldset className="create-form__fields" disabled={submitting}>
        <label className="create-form__field">
          <span className="create-form__label">Title</span>
          <input
            className="create-form__input"
            value={title}
            maxLength={120}
            placeholder="ATM out of service"
            onChange={(e) => setTitle(e.target.value)}
            {...fieldProps('title')}
          />
          {renderError('title')}
        </label>
        <label className="create-form__field">
          <span className="create-form__label">Asset code</span>
          <input
            className="create-form__input"
            value={assetCode}
            maxLength={40}
            placeholder="ATM-0451"
            onChange={(e) => setAssetCode(e.target.value.toUpperCase())}
            {...fieldProps('assetCode')}
          />
          {renderError('assetCode')}
        </label>
        <label className="create-form__field">
          <span className="create-form__label">Priority</span>
          <select
            className="create-form__input"
            value={priority}
            onChange={(e) => setPriority(e.target.value as Priority)}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABEL[p]}
              </option>
            ))}
          </select>
        </label>
        <label className="create-form__field">
          <span className="create-form__label">Description</span>
          <textarea
            className="create-form__input create-form__textarea"
            value={description}
            maxLength={1000}
            rows={3}
            placeholder="Screen shows no response"
            onChange={(e) => setDescription(e.target.value)}
            {...fieldProps('description')}
          />
          {renderError('description')}
        </label>
        <label className="create-form__field">
          <span className="create-form__label">Reported by</span>
          <input
            className="create-form__input"
            value={reportedBy}
            maxLength={100}
            onChange={(e) => setReportedBy(e.target.value)}
            {...fieldProps('reportedBy')}
          />
          {renderError('reportedBy')}
        </label>
      </fieldset>
      {formError && (
        <p className="create-form__error" role="alert">
          {formError}
        </p>
      )}
      <button type="submit" className="create-form__submit" disabled={submitting}>
        {submitting && <span className="create-form__spinner" aria-hidden="true" />}
        {submitting ? 'Creating…' : 'Create ticket'}
      </button>
    </form>
  )
}
