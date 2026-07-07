export function SkeletonLine({ width = '100%', height = 14 }: { width?: string; height?: number }) {
  return (
    <div
      className="skeleton"
      style={{ width, height, marginBottom: 8 }}
    />
  );
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bento-card space-y-2">
      <SkeletonLine width="60%" height={16} />
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine key={i} width={`${70 + Math.random() * 30}%`} />
      ))}
    </div>
  );
}

export function LoadingSpinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-lumina-400 rounded-full animate-spin" style={{ borderTopColor: 'transparent' }} />
        {label && <p className="text-xs text-slate-500">{label}</p>}
      </div>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }: {
  icon: React.FC<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-lumina-400/10 to-lumina-600/10 border border-lumina-500/20 flex items-center justify-center mb-4">
        <Icon className="w-7 h-7 text-lumina-400/60" />
      </div>
      <p className="text-sm text-slate-300 font-medium">{title}</p>
      {description && <p className="text-xs text-slate-500 mt-1 max-w-sm">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-3">
        <span className="text-red-400 text-xl">!</span>
      </div>
      <p className="text-sm text-slate-300">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 text-xs text-lumina-400 hover:text-lumina-300 transition-colors">
          Try again
        </button>
      )}
    </div>
  );
}
