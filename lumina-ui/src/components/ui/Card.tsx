import React from 'react';

/* ── Card ── */
interface CardProps { children: React.ReactNode; className?: string; hover?: boolean; onClick?: () => void; }
export default function Card({ children, className = '', hover = true, onClick }: CardProps) {
  return (
    <div onClick={onClick} className={`card ${hover ? 'cursor-pointer' : ''} ${className}`}>
      {children}
    </div>
  );
}
export function CardSection({ label, children, action }: { label?: string; children: React.ReactNode; action?: React.ReactNode; }) {
  return (
    <div className="space-y-3">
      {label && (
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider">{label}</h2>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

/* ── Button ── */
type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  loading?: boolean;
  children?: React.ReactNode;
}
export function Button({ variant = 'primary', size = 'md', icon, loading, children, className = '', disabled, ...props }: ButtonProps) {
  const sizeClass = size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : '';
  return (
    <button className={`btn btn-${variant} ${sizeClass} ${className}`} disabled={disabled || loading} {...props}>
      {loading ? <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" /> : icon}
      {children}
    </button>
  );
}

/* ── Input ── */
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helper?: string;
  error?: string;
  icon?: React.ReactNode;
}
export function Input({ label, helper, error, icon, className = '', ...props }: InputProps) {
  return (
    <div className="input-group">
      {label && <label className="input-label">{label}</label>}
      <div className="relative">
        <input className={`input ${error ? '!border-red-500' : ''} ${icon ? 'pl-8' : ''} ${className}`} {...props} />
        {icon && <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]">{icon}</span>}
      </div>
      {helper && !error && <span className="input-helper">{helper}</span>}
      {error && <span className="input-error">{error}</span>}
    </div>
  );
}

/* ── Select ── */
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}
export function Select({ label, options, className = '', ...props }: SelectProps) {
  return (
    <div className="input-group">
      {label && <label className="input-label">{label}</label>}
      <select className={`select ${className}`} {...props}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

/* ── Badge ── */
type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'brand';
export function Badge({ variant = 'info', children }: { variant?: BadgeVariant; children: React.ReactNode }) {
  return <span className={`badge badge-${variant}`}>{children}</span>;
}

/* ── Modal ── */
interface ModalProps { open: boolean; onClose: () => void; title?: string; wide?: boolean; children: React.ReactNode; }
export function Modal({ open, onClose, title, wide, children }: ModalProps) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className={`modal-dialog ${wide ? 'wide' : ''}`} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">{title}</h3>
          <button onClick={onClose} className="btn btn-ghost btn-icon">&times;</button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ── Table ── */
interface Column<T> { key: string; label: string; render?: (row: T) => React.ReactNode; className?: string; }
interface TableProps<T> { columns: Column<T>[]; data: T[]; rowKey: (row: T) => string; onRowClick?: (row: T) => void; }
export function Table<T extends Record<string, any>>({ columns, data, rowKey, onRowClick }: TableProps<T>) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map(c => <th key={c.key} className={c.className}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={rowKey(row)} onClick={() => onRowClick?.(row)} className={onRowClick ? 'cursor-pointer' : ''}>
              {columns.map(c => <td key={c.key} className={c.className}>{c.render ? c.render(row) : row[c.key]}</td>)}
            </tr>
          ))}
          {data.length === 0 && (
            <tr><td colSpan={columns.length} className="text-center py-8 text-[var(--text-tertiary)]">No data</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

/* ── Tabs ── */
interface TabsProps { tabs: { id: string; label: string; icon?: React.ReactNode }[]; active: string; onChange: (id: string) => void; }
export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="tabs">
      {tabs.map(t => (
        <button key={t.id} className={`tab ${active === t.id ? 'active' : ''}`} onClick={() => onChange(t.id)}>
          {t.icon && <span className="mr-1.5">{t.icon}</span>}{t.label}
        </button>
      ))}
    </div>
  );
}

/* ── Dropdown ── */
interface DropdownItem { label: string; icon?: React.ReactNode; onClick: () => void; danger?: boolean; }
export function Dropdown({ items, open, children }: { items: (DropdownItem | 'separator')[]; open: boolean; children: React.ReactNode }) {
  return (
    <div className="tooltip-wrap">
      {children}
      {open && (
        <div className="dropdown">
          {items.map((item, i) => item === 'separator'
            ? <div key={i} className="dropdown-separator" />
            : <button key={i} className={`dropdown-item ${item.danger ? '!text-red-400' : ''}`} onClick={item.onClick}>
                {item.icon}{item.label}
              </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Tooltip ── */
export function Tooltip({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <div className="tooltip-wrap">
      {children}
      <span className="tooltip">{text}</span>
    </div>
  );
}

/* ── Checkbox ── */
export function Checkbox({ checked, onChange, label }: { checked: boolean; onChange: (checked: boolean) => void; label?: string }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)}
        className="w-3.5 h-3.5 rounded border-[var(--border-secondary)] bg-transparent accent-[var(--brand-500)] cursor-pointer" />
      {label && <span className="text-sm text-[var(--text-secondary)]">{label}</span>}
    </label>
  );
}
