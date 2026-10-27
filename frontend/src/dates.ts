// Mirrors the backend range (backend/app/domain/limits.py).
export const MIN_DATE = '2000-01-01'
export const MAX_DATE = '2099-12-31'

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/

/** True for a real calendar date (YYYY-MM-DD) inside the accepted range. */
export function isValidDate(value: string): boolean {
  if (!DATE_RE.test(value) || value < MIN_DATE || value > MAX_DATE) return false
  const parsed = new Date(`${value}T00:00:00Z`)
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value
}
