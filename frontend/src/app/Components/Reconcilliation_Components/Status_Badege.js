import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, XCircle, AlertCircle } from "lucide-react";

const statusConfig = {
  completed: {
    icon: CheckCircle,
    color: "bg-emerald-100 text-emerald-700 border-emerald-200",
    label: "Completed",
  },
  processing: {
    icon: Clock,
    color: "bg-blue-100 text-blue-700 border-blue-200",
    label: "Processing",
  },
  failed: {
    icon: XCircle,
    color: "bg-red-100 text-red-700 border-red-200",
    label: "Failed",
  },
  pending_review: {
    icon: AlertCircle,
    color: "bg-amber-100 text-amber-700 border-amber-200",
    label: "Pending Review",
  },
};

export default function StatusBadge({ status }) {
  const cfg = statusConfig[status] || {};
  const Icon = cfg.icon || Clock;

  return (
    <Badge variant="secondary" className={`${cfg.color || ""} border flex items-center gap-1 w-fit`}>
      <Icon className="w-3 h-3" />
      {cfg.label || status}
    </Badge>
  );
}
