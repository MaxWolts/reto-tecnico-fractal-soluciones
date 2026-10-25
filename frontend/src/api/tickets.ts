import { get, post, put } from './client'
import type {
  CreateTicketInput,
  HistoryEvent,
  Notification,
  Operator,
  Ticket,
  TicketFilters,
  Transition,
  TransitionInput,
} from '../types'

export interface Health {
  status: string
  database: 'ok' | 'down'
}

export const getHealth = () => get<Health>('/health')
export const listOperators = () => get<Operator[]>('/api/operators')
export const listTransitions = () => get<Transition[]>('/api/transitions')

export const createTicket = (input: CreateTicketInput) => post<Ticket>('/api/tickets', input)
export const listTickets = (filters: TicketFilters = {}) => get<Ticket[]>('/api/tickets', { ...filters })
export const getTicket = (id: number) => get<Ticket>(`/api/tickets/${id}`)
export const getTicketHistory = (id: number) => get<HistoryEvent[]>(`/api/tickets/${id}/history`)

export const transitionTicket = (id: number, input: TransitionInput) =>
  post<Ticket>(`/api/tickets/${id}/transitions`, input)

export const addComment = (id: number, comment: string, actor: string) =>
  post<HistoryEvent>(`/api/tickets/${id}/comments`, { comment, actor })

export const assignTicket = (id: number, operatorId: number | null, actor: string, version: number) =>
  put<Ticket>(`/api/tickets/${id}/assignee`, { operatorId, actor, version })

export const listNotifications = (since?: string, limit = 20) =>
  get<Notification[]>('/api/notifications', { since, limit })
