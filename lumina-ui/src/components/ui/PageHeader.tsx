import type { FC } from 'react';

interface PageHeaderProps {
  icon: FC<{ className?: string }>;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  status?: React.ReactNode;
}

export default function PageHeader({ icon: Icon, title, description, actions, status }: PageHeaderProps) {
  return (
    <div className="flex items-center gap-3 pb-5 border-b border-white/5 shrink-0">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center shadow-lg shadow-lumina-500/20">
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {description && <p className="text-xs text-slate-400 truncate">{description}</p>}
      </div>
      {status && <div className="shrink-0">{status}</div>}
      {actions && <div className="shrink-0 flex items-center gap-2">{actions}</div>}
    </div>
  );
}
