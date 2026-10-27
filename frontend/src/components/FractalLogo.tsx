import { useId } from 'react'
import './FractalLogo.css'

/* Letters are stroked paths (4 units wide) on a 24 unit high baseline; the two A are hollow triangles (even-odd fill cuts the inner one out). */
export function FractalLogo() {
  const titleId = useId()
  return (
    <svg
      className="fractal-logo"
      viewBox="0 0 170 24"
      role="img"
      aria-labelledby={titleId}
      focusable="false"
    >
      <title id={titleId}>Fractal</title>
      <g className="fractal-logo__letters" aria-hidden="true">
        <path d="M2 24V2H16M2 12H14" />
        <path d="M24 24V2H33A5.5 5.5 0 0 1 33 13H24M32 13L39 24" />
        <path d="M94.07 4.93A10 10 0 1 0 94.07 19.07" />
        <path d="M103 2H121M112 2V24" />
        <path d="M157 0V22H170" />
      </g>
      <g className="fractal-logo__a" aria-hidden="true">
        <path d="M47 24L58 0L69 24ZM53.5 20.5L58 11L62.5 20.5Z" />
        <path d="M127 24L138 0L149 24ZM133.5 20.5L138 11L142.5 20.5Z" />
      </g>
    </svg>
  )
}
