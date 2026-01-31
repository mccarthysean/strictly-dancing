// Toast component wrapper for Sonner
// Use the Toaster from @/components/ui/sonner in your app root
// Use the toast function from sonner for showing toasts

import { toast } from 'sonner'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  description?: string
  duration?: number
}

// Convenience functions for showing toasts
export function showToast(message: string, type: ToastType = 'info', options?: ToastOptions) {
  switch (type) {
    case 'success':
      toast.success(message, options)
      break
    case 'error':
      toast.error(message, options)
      break
    case 'warning':
      toast.warning(message, options)
      break
    case 'info':
    default:
      toast.info(message, options)
      break
  }
}

export function showError(message: string, options?: ToastOptions) {
  toast.error(message, { duration: 6000, ...options })
}

export function showSuccess(message: string, options?: ToastOptions) {
  toast.success(message, { duration: 4000, ...options })
}

export function showWarning(message: string, options?: ToastOptions) {
  toast.warning(message, { duration: 5000, ...options })
}

export function showInfo(message: string, options?: ToastOptions) {
  toast.info(message, { duration: 5000, ...options })
}

// Re-export the toast function for direct usage
export { toast }
