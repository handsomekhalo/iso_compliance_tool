export default function ActivitySkeleton() {
  return (
    <div className="space-y-4">
      {Array(5).fill(0).map((_, i) => (
        <div key={i} className="flex items-center gap-4 animate-pulse">
          <div className="w-12 h-12 bg-slate-200 rounded-full" />
          <div className="flex-1">
            <div className="h-4 bg-slate-200 rounded w-32 mb-2" />
            <div className="h-3 bg-slate-200 rounded w-48" />
          </div>
          <div className="h-6 bg-slate-200 rounded w-20" />
        </div>
      ))}
    </div>
  );
}
