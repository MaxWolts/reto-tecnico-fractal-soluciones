import { useRef } from 'react'
import { createPortal } from 'react-dom'
import { useBodyScrollLock } from '../hooks/useBodyScrollLock'
import { useClosing } from '../hooks/useClosing'
import { useModal } from '../hooks/useModal'
import type { Ticket } from '../types'
import { CreateTicketForm } from './CreateTicketForm'
import { XmarkIcon } from './Icons'
import './NewTicketSheet.css'

interface NewTicketSheetProps {
  currentUser: string
  onCreated: (ticket: Ticket) => void
  onClose: () => void
}

/** Bottom sheet that hosts the create form on small screens. */
export function NewTicketSheet({ currentUser, onCreated, onClose }: NewTicketSheetProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [closing, requestClose] = useClosing(onClose)
  const onKeyDown = useModal(ref, requestClose)
  useBodyScrollLock()

  return createPortal(
    <div
      className={`sheet__backdrop${closing ? ' sheet__backdrop--closing' : ''}`}
      onMouseDown={(e) => e.target === e.currentTarget && requestClose()}
    >
      <div
        ref={ref}
        className={`sheet${closing ? ' sheet--closing' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="New ticket"
        tabIndex={-1}
        onKeyDown={onKeyDown}
      >
        <div className="sheet__bar">
          <span className="sheet__grabber" aria-hidden="true" />
          <button type="button" className="icon-btn" aria-label="Close new ticket form" onClick={requestClose}>
            <XmarkIcon />
          </button>
        </div>
        <CreateTicketForm
          currentUser={currentUser}
          onCreated={(t) => {
            onCreated(t)
            requestClose()
          }}
        />
      </div>
    </div>,
    document.body,
  )
}
