import './Button.css'

export default function Button({ variant = 'primary', loading = false, loadingLabel = 'Memproses…', disabled = false, fullWidth = true, className = '', children, type = 'button', ...props }) {
  return <button {...props} type={type} className={`action-button action-button--${variant}${fullWidth ? ' action-button--full' : ''} ${className}`.trim()} disabled={disabled || loading} aria-busy={loading || undefined}>
    {loading ? <><span className="button-spinner" aria-hidden="true" /><span>{loadingLabel}</span></> : children}
  </button>
}
