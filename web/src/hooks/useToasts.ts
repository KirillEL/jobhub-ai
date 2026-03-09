import { useState } from 'react'
import type { ToastMessage, ToastType } from '../components/common/ToastStack'

export function useToasts() {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  function pushToast(type: ToastType, title: string, description?: string): void {
    const id = Date.now() + Math.floor(Math.random() * 1000)
    setToasts((prev) => [...prev, { id, type, title, description }])
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id))
    }, 4500)
  }

  function removeToast(id: number): void {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }

  return { toasts, pushToast, removeToast }
}
