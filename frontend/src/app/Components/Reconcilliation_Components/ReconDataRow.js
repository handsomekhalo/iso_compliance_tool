import { TableCell } from "@/components/ui/table";
import { motion } from "framer-motion";
import { FileText } from "lucide-react";
import { format } from "date-fns";

import StatusBadge from "./Status_Badege";



export default function ReconDataRow({ recon, index }) {
  return (
    <motion.tr
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="hover:bg-slate-50 transition-colors cursor-pointer"
    >
      <TableCell className="font-medium text-slate-900">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-slate-400" />
          {recon.file_name}
        </div>
      </TableCell>

      <TableCell className="text-slate-600">
        {format(new Date(recon.upload_date), "MMM d, yyyy HH:mm")}
      </TableCell>

      <TableCell className="text-slate-600">
        <div className="flex items-center gap-1">
          <span className="font-medium">{recon.matched_records || 0}</span>
          <span className="text-slate-400">/</span>
          <span className="text-slate-400">{recon.total_records || 0}</span>
        </div>
      </TableCell>

      <TableCell>
        <span
          className={`font-semibold ${
            recon.accuracy >= 95
              ? "text-emerald-600"
              : recon.accuracy >= 85
              ? "text-amber-600"
              : "text-red-600"
          }`}
        >
          {recon.accuracy?.toFixed(1)}%
        </span>
      </TableCell>

      <TableCell className="font-medium text-slate-900">
        ${recon.total_amount?.toLocaleString() || "0"}
      </TableCell>

      <TableCell>
        <StatusBadge status={recon.status} />
      </TableCell>
    </motion.tr>
  );
}
