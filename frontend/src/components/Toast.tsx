import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  message: string
  type: ToastType
  duration: number
}

interface ToastContextValue {
  toasts: Toast[]
  showToast: (message: string, type?: ToastType, duration?: number) => void
  showError: (message: string) => void
  showSuccess: (message: string) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

interface ToastProviderProps {
  children: ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  const showToast = useCallback((message: string, type: ToastType = 'info', duration = 5000) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    const toast: Toast = { id, message, type, duration }

    setToasts(prev => [...prev, toast])

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
  }, [removeToast])

  const showError = useCallback((message: string) => {
    showToast(message, 'error', 6000)
  }, [showToast])

  const showSuccess = useCallback((message: string) => {
    showToast(message, 'success', 4000)
  }, [showToast])

  const value: ToastContextValue = {
    toasts,
    showToast,
    showError,
    showSuccess,
    removeToast,
  }

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div style={containerStyles.container}>
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  )
}

interface ToastItemProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const typeStyles = getTypeStyles(toast.type)

  return (
    <div
      style={{
        ...itemStyles.toast,
        ...typeStyles.container,
      }}
      role="alert"
    >
      <span style={typeStyles.icon}>{getIcon(toast.type)}</span>
      <span style={itemStyles.message}>{toast.message}</span>
      <button
        type="button"
        onClick={() => onRemove(toast.id)}
        style={itemStyles.closeButton}
        aria-label="Dismiss"
      >
        &#10005;
      </button>
    </div>
  )
}

function getIcon(type: ToastType): string {
  switch (type) {
    case 'success': return '✓'
    case 'error': return '✕'
    case 'warning': return '⚠'
    case 'info': return 'ℹ'
    default: return 'ℹ'
  }
}

function getTypeStyles(type: ToastType) {
  switch (type) {
    case 'success':
      return {
        container: { backgroundColor: '#d1fae5', borderColor: '#10b981' },
        icon: { color: '#059669', fontWeight: 700 as const },
      }
    case 'error':
      return {
        container: { backgroundColor: '#fee2e2', borderColor: '#ef4444' },
        icon: { color: '#dc2626', fontWeight: 700 as const },
      }
    case 'warning':
      return {
        container: { backgroundColor: '#fef3c7', borderColor: '#f59e0b' },
        icon: { color: '#d97706', fontWeight: 700 as const },
      }
    case 'info':
    default:
      return {
        container: { backgroundColor: '#dbeafe', borderColor: '#3b82f6' },
        icon: { color: '#2563eb', fontWeight: 700 as const },
      }
  }
}

const containerStyles: Record<string, React.CSSProperties> = {
  container: {
    position: 'fixed',
    bottom: '1rem',
    right: '1rem',
    left: '1rem',
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '0.75rem',
    pointerEvents: 'none',
  },
}

const itemStyles: Record<string, React.CSSProperties> = {
  toast: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.875rem 1rem',
    borderRadius: '10px',
    borderLeft: '4px solid',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    maxWidth: '400px',
    width: '100%',
    pointerEvents: 'auto',
    animation: 'slideIn 0.3s ease-out',
  },
  message: {
    flex: 1,
    fontSize: '0.9375rem',
    color: '#1f2937',
    lineHeight: 1.4,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    padding: '0.25rem',
    cursor: 'pointer',
    fontSize: '0.875rem',
    color: '#6b7280',
    opacity: 0.7,
    lineHeight: 1,
  },
}

export default ToastProvider
