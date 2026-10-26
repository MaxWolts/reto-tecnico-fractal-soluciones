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
