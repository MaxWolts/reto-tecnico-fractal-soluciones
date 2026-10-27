import { useCallback, useState } from 'react'

export type ThemeChoice = 'light' | 'dark'

const KEY = 'theme'

function read(): ThemeChoice {
  try {
    const v = localStorage.getItem(KEY)
    if (v === 'light' || v === 'dark') return v
  } catch {
    /* storage unavailable */
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function apply(choice: ThemeChoice) {
  document.documentElement.setAttribute('data-theme', choice)
  try {
    localStorage.setItem(KEY, choice)
  } catch {
    /* storage unavailable */
  }
}

/** Light / dark choice, persisted and mirrored as data-theme on <html>. */
export function useTheme() {
  const [theme, setTheme] = useState<ThemeChoice>(read)
  const cycle = useCallback(() => {
    const next: ThemeChoice = theme === 'light' ? 'dark' : 'light'
    apply(next)
    setTheme(next)
  }, [theme])
  return { theme, cycle }
}
