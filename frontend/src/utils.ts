import type { Priority, TicketStatus } from './types'

export const STATUS_LABEL: Record<TicketStatus, string> = {
  PENDING: 'Pending',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
  CANCELLED: 'Cancelled',
}

export const PRIORITY_LABEL: Record<Priority, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  CRITICAL: 'Critical',
}

const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * 24 * 3600],
  ['month', 30 * 24 * 3600],
  ['day', 24 * 3600],
  ['hour', 3600],
  ['minute', 60],
]

export function relativeTime(iso: string, now: number = Date.now()): string {
  const time = new Date(iso).getTime()
  if (Number.isNaN(time)) return ''
  const diffSeconds = Math.round((time - now) / 1000)
  for (const [unit, seconds] of UNITS) {
    if (Math.abs(diffSeconds) >= seconds) return rtf.format(Math.trunc(diffSeconds / seconds), unit)
  }
  return 'just now'
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  const first = parts[0][0]
  const last = parts.length > 1 ? parts[parts.length - 1][0] : (parts[0][1] ?? '')
  return (first + last).toUpperCase()
}

export function transitionLabel(from: TicketStatus, to: TicketStatus): string {
  if (to === 'CANCELLED') return 'Cancel ticket'
  if (from === 'PENDING' && to === 'IN_PROGRESS') return 'Start work'
  if (from === 'IN_PROGRESS' && to === 'RESOLVED') return 'Resolve'
  if (from === 'IN_PROGRESS' && to === 'PENDING') return 'Send back to pending'
  return `Move to ${STATUS_LABEL[to]}`
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString()
}

export function statusModifier(status: TicketStatus): string {
  return status.toLowerCase().replace('_', '-')
}
