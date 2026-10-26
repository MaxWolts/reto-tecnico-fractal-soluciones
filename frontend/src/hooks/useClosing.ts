import { useCallback, useEffect, useRef, useState } from 'react'

export const CLOSE_MS = 200

/**
 * Exit animation helper: `requestClose` flips `closing` (apply an exit class)
 * and calls `onClose` once the animation time has passed.
 */
export function useClosing(onClose: () => void) {
  const [closing, setClosing] = useState(false)
  const timer = useRef<number | undefined>(undefined)
  const closeRef = useRef(onClose)
  useEffect(() => {
    closeRef.current = onClose
  })
  useEffect(() => () => window.clearTimeout(timer.current), [])

  const requestClose = useCallback(() => {
    if (timer.current !== undefined) return
    setClosing(true)
    timer.current = window.setTimeout(() => closeRef.current(), CLOSE_MS)
  }, [])

  return [closing, requestClose] as const
}
