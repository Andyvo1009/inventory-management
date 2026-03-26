import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export interface FilterOption {
  value: string | number;
  label: string;
}

interface FilterSelectProps {
  value: string | number | null;
  onChange: (value: string | number | null) => void;
  options: FilterOption[];
  placeholder: string;
}

export default function FilterSelect({ value, onChange, options, placeholder }: FilterSelectProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const selectedLabel = value !== null ? options.find((o) => o.value === value)?.label : null;
  const isActive = value !== null;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
          isActive
            ? 'bg-blue-500/15 text-blue-300 border border-blue-500/40'
            : 'bg-white/5 text-slate-400 border border-white/8 hover:bg-white/10 hover:text-slate-200'
        }`}
      >
        <span>{selectedLabel ?? placeholder}</span>
        <ChevronDown
          size={12}
          className={`shrink-0 transition-transform duration-150 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute left-0 top-full mt-1.5 z-50 min-w-[180px] overflow-hidden rounded-lg border border-white/10 bg-slate-800 shadow-2xl shadow-black/40 py-1">
          {/* "All" / reset option */}
          <button
            onClick={() => { onChange(null); setOpen(false); }}
            className={`flex w-full items-center justify-between px-3 py-2 text-xs transition-colors ${
              value === null
                ? 'bg-blue-500/10 text-blue-300'
                : 'text-slate-400 hover:bg-white/5 hover:text-white'
            }`}
          >
            {placeholder}
            {value === null && <Check size={12} className="shrink-0" />}
          </button>

          {options.length > 0 && <div className="my-1 h-px bg-white/5" />}

          {options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => { onChange(opt.value); setOpen(false); }}
              className={`flex w-full items-center justify-between px-3 py-2 text-xs transition-colors ${
                value === opt.value
                  ? 'bg-blue-500/10 text-blue-300'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              {opt.label}
              {value === opt.value && <Check size={12} className="shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
