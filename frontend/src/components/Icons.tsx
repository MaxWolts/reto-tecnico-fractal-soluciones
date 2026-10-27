const SVG_PROPS = {
  viewBox: '0 0 24 24',
  'aria-hidden': true,
  focusable: false,
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
} as const

export function XmarkIcon({ size = 20 }: { size?: number }) {
  return (
    <svg {...SVG_PROPS} width={size} height={size}>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  )
}

export function PencilIcon({ size = 14 }: { size?: number }) {
  return (
    <svg {...SVG_PROPS} width={size} height={size}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  )
}

export function SunIcon({ size = 20 }: { size?: number }) {
  return (
    <svg {...SVG_PROPS} width={size} height={size}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  )
}

export function MoonIcon({ size = 20 }: { size?: number }) {
  return (
    <svg {...SVG_PROPS} width={size} height={size}>
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
    </svg>
  )
}
