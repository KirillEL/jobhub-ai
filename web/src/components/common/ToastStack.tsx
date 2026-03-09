import { useI18n } from '../../shared/i18n'
import './styles.scss'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: number
  type: ToastType
  title: string
  description?: string
}

interface ToastStackProps {
  toasts: ToastMessage[]
  onClose: (id: number) => void
}

export default function ToastStack({ toasts, onClose }: ToastStackProps) {
  const { t } = useI18n()

  return (
    <div className="toast-stack" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast--${toast.type}`}>
          <div className="toast__content">
            <strong>{toast.title}</strong>
            {toast.description ? <span>{toast.description}</span> : null}
          </div>
          <button className="toast__close" onClick={() => onClose(toast.id)} aria-label={t('common.close')}>
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
