import { useTheme } from '../hooks/useTheme'
import { MoonIcon, SunIcon } from './Icons'

export function ThemeToggle() {
  const { theme, cycle } = useTheme()
  const label = theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'
  return (
    <button type="button" className="icon-btn" aria-label={label} title={label} onClick={cycle}>
      {theme === 'light' ? <MoonIcon /> : <SunIcon />}
    </button>
  )
}
