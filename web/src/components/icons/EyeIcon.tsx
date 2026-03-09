import './styles.scss'

interface EyeIconProps {
  visible: boolean
}

export default function EyeIcon({ visible }: EyeIconProps) {
  return (
    <svg className="eye-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M2.1 12c1.73-3.53 5.3-6 9.9-6s8.17 2.47 9.9 6c-1.73 3.53-5.3 6-9.9 6s-8.17-2.47-9.9-6Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.8" />
      {!visible ? (
        <path
          d="M4 4l16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      ) : null}
    </svg>
  )
}
