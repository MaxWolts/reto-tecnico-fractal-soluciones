import { useEffect } from 'react'

let locks = 0
let previousOverflow = ''

/** Locks page scroll while the calling component is mounted. Nested locks are counted. */
export function useBodyScrollLock() {
  useEffect(() => {
    if (locks === 0) {
      previousOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
    }
    locks += 1
    return () => {
      locks -= 1
      if (locks === 0) document.body.style.overflow = previousOverflow
    }
  }, [])
}
