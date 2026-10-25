import { useEffect, useState } from 'react'
import { listOperators } from '../api/tickets'
import type { Operator } from '../types'

export function useOperators(): Operator[] {
  const [operators, setOperators] = useState<Operator[]>([])
  useEffect(() => {
    let active = true
    listOperators()
      .then((data) => {
        if (active) setOperators(data)
      })
      .catch(() => {
        // Non-critical: the operator filter and assignee select just stay empty.
      })
    return () => {
      active = false
    }
  }, [])
  return operators
}
