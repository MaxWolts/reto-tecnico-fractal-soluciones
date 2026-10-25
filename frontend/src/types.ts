export type TicketStatus = 'PENDING' | 'IN_PROGRESS' | 'RESOLVED' | 'CANCELLED'
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type HistoryEventType = 'CREATED' | 'STATUS_CHANGED' | 'COMMENT' | 'ASSIGNED'
export type Role = 'Reporter' | 'Operator'

export const STATUSES: TicketStatus[] = ['PENDING', 'IN_PROGRESS', 'RESOLVED', 'CANCELLED']
export const PRIORITIES: Priority[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export interface AllowedTransition {
  toStatus: TicketStatus
  requiresDiagnosis: boolean
  requiresComment: boolean
}

export interface Transition extends AllowedTransition {
  fromStatus: TicketStatus
}

export interface Ticket {
  id: number
  code: string
  title: string
  description: string | null
  assetCode: string
  priority: Priority
  status: TicketStatus
  diagnosis: string | null
  assignedOperator: { id: number; name: string } | null
  reportedBy: string
  createdAt: string
  updatedAt: string
  version: number
  allowedTransitions: AllowedTransition[]
}

export interface HistoryEvent {
  id: number
  ticketId: number
  eventType: HistoryEventType
  fromStatus: TicketStatus | null
  toStatus: TicketStatus | null
  comment: string | null
  actor: string
  createdAt: string
}

export interface Operator {
  id: number
  name: string
  email: string
}

export interface Notification {
  id: number
  ticketId: number
  ticketTitle: string
  fromStatus: TicketStatus | null
  toStatus: TicketStatus | null
  actor: string
  createdAt: string
}

export interface FieldError {
  field: string
  message: string
}

export interface ProblemDetails {
  type?: string
  title?: string
  status: number
  detail?: string
  code?: string
  errors?: FieldError[]
}

export interface CreateTicketInput {
  title: string
  description?: string
  assetCode: string
  priority?: Priority
  reportedBy: string
}

export interface TicketFilters {
  status?: TicketStatus
  priority?: Priority
  operatorId?: number
  from?: string
  to?: string
  q?: string
}

export interface TransitionInput {
  toStatus: TicketStatus
  diagnosis?: string
  comment?: string
  actor: string
  version: number
}
