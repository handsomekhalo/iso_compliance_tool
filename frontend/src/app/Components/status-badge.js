const STYLES = {
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  sent: "bg-blue-50 text-blue-700 border-blue-200",
  settled: "bg-emerald-50 text-emerald-700 border-emerald-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  expired: "bg-gray-50 text-gray-600 border-gray-200",
  processing: "bg-amber-50 text-amber-700 border-amber-200",
};

export function StatusBadge({ status }) {
  const style = STYLES[status] ?? "bg-gray-50 text-gray-600 border-gray-200";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize ${style}`}
    >
      {status}
    </span>
  );
}
