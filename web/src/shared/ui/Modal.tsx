import Button from './Button'
import { useI18n } from '../i18n'

interface ModalProps {
  title: string
  text: string
  onConfirm: () => void
  onCancel: () => void
  confirmLabel?: string
  cancelLabel?: string
  loading?: boolean
}

export default function Modal({
  title,
  text,
  onConfirm,
  onCancel,
  confirmLabel,
  cancelLabel,
  loading = false,
}: ModalProps) {
  const { t } = useI18n()
  const resolvedConfirmLabel = confirmLabel ?? t('common.confirm')
  const resolvedCancelLabel = cancelLabel ?? t('common.cancel')

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <h3>{title}</h3>
        <p>{text}</p>
        <div className="modal__actions">
          <Button variant="secondary" onClick={onCancel} disabled={loading}>
            {resolvedCancelLabel}
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={loading}>
            {loading ? t('common.processing') : resolvedConfirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
