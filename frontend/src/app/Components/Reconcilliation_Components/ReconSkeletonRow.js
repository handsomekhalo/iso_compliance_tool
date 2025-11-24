import { TableRow, TableCell } from "@/components/ui/table";

export default function ReconSkeletonRow() {
  return (
    <TableRow className="animate-pulse">
      <TableCell><div className="h-4 bg-slate-200 rounded w-32" /></TableCell>
      <TableCell><div className="h-4 bg-slate-200 rounded w-24" /></TableCell>
      <TableCell><div className="h-4 bg-slate-200 rounded w-16" /></TableCell>
      <TableCell><div className="h-4 bg-slate-200 rounded w-16" /></TableCell>
      <TableCell><div className="h-4 bg-slate-200 rounded w-20" /></TableCell>
      <TableCell><div className="h-6 bg-slate-200 rounded-full w-24" /></TableCell>
    </TableRow>
  );
}
