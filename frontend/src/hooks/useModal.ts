import { useEffect, useRef, type KeyboardEvent, type RefObject } from 'react'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

/**
 * Simple modal behaviour: moves focus inside on mount, restores it on unmount,
 * closes on Esc and keeps Tab within the container. Attach the returned
 * handler to the container's onKeyDown. Handled keys do not bubble, so a
 * nested modal only affects itself.
 */
export function useModal(ref: RefObject<HTMLElement | null>, onClose: () => void) {
  const closeRef = useRef(onClose)
  useEffect(() => {
    closeRef.current = onClose
  })

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const container = ref.current
    if (container) {
      const target = container.querySelector<HTMLElement>('[data-autofocus]') ?? container.querySelector<HTMLElement>(FOCUSABLE)
      ;(target ?? container).focus()
    }
    return () => previous?.focus?.()
  }, [ref])

  return (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === 'Escape') {
      event.stopPropagation()
      closeRef.current()
      return
    }
    if (event.key !== 'Tab' || !ref.current) return
    event.stopPropagation()
    const items = Array.from(ref.current.querySelectorAll<HTMLElement>(FOCUSABLE))
    if (items.length === 0) {
      event.preventDefault()
      return
    }
    const first = items[0]
    const last = items[items.length - 1]
    const active = document.activeElement
    if (event.shiftKey && (active === first || active === ref.current)) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && active === last) {
      event.preventDefault()
      first.focus()
    }
  }
}
