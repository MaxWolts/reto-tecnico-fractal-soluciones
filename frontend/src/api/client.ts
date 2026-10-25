import type { FieldError, ProblemDetails } from '../types'

const BASE_URL: string = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  code: string
  detail: string
  errors: FieldError[]

  constructor(problem: ProblemDetails) {
    const detail = problem.detail ?? problem.title ?? 'Unexpected error'
    super(detail)
    this.name = 'ApiError'
    this.status = problem.status
    this.code = problem.code ?? 'UNKNOWN'
    this.detail = detail
    this.errors = problem.errors ?? []
  }
}

type Query = Record<string, string | number | undefined | null>

function buildUrl(path: string, query?: Query): string {
  const url = new URL(path, BASE_URL)
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value))
    }
  }
  return url.toString()
}

export async function request<T>(
  method: 'GET' | 'POST' | 'PUT',
  path: string,
  options: { query?: Query; body?: unknown } = {},
): Promise<T> {
  let response: Response
  try {
    response = await fetch(buildUrl(path, options.query), {
      method,
      headers: {
        Accept: 'application/json',
        ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      },
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    throw new ApiError({
      status: 0,
      code: 'NETWORK_ERROR',
      detail: 'Cannot reach the server. Check your connection and try again.',
    })
  }

  if (!response.ok) {
    let problem: ProblemDetails
    try {
      problem = (await response.json()) as ProblemDetails
      if (typeof problem.status !== 'number') problem.status = response.status
    } catch {
      problem = { status: response.status, detail: response.statusText || 'Request failed' }
    }
    throw new ApiError(problem)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const get = <T>(path: string, query?: Query) => request<T>('GET', path, { query })
export const post = <T>(path: string, body: unknown) => request<T>('POST', path, { body })
export const put = <T>(path: string, body: unknown) => request<T>('PUT', path, { body })
