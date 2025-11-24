"use client";

import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, XCircle } from "lucide-react";


const ICONS = { CheckCircle, Clock, XCircle };

export default function StatusActivityBadge({ status }) {
  const config = statusConfig[status] || {};
  const Icon = ICONS[config.icon] || Clock;

  return (
    <Badge
      variant="secondary"
      className={`${config.color || ""} border flex items-center gap-1 shrink-0`}
    >
      <Icon className="w-3 h-3" />
      {status}
    </Badge>
  );
}
