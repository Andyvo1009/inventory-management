import { AlertCircle, X } from 'lucide-react';

interface ErrorBoxProps {
  message: string;
  title?: string;
  onClose?: () => void;
  className?: string;
}

export default function ErrorBox({
  message,
  title = 'Something went wrong',
  onClose,
  className = '',
}: ErrorBoxProps) {
  return (
    <div
      className={`rounded-xl border border-rose-300 bg-rose-100 p-4 text-black ${className}`.trim()}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        <AlertCircle size={18} className="mt-0.5 shrink-0 text-black" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-black">{title}</p>
          <p className="mt-1 text-sm text-black break-words">{message}</p>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-black/80 transition-colors hover:bg-black/10 hover:text-black"
            aria-label="Dismiss error"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
