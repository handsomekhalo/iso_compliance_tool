import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell} from "@/components/ui/table";
import { FileText } from "lucide-react";
// import { motion } from "framer-motion";
// import { format } from "date-fns";

// import StatusBadge from "./Status_Badege";
import ReconSkeletonRow from "./ReconSkeletonRow";
import ReconDataRow from "./ReconDataRow";

export default function ReconciliationsTable({ reconciliations = [], isLoading }) {
  return (
    <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
      <CardHeader className="border-b border-slate-100 pb-4">
        <CardTitle className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-amber-600" />
          Recent Reconciliations
        </CardTitle>
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50 hover:bg-slate-50">
                {["File Name", "Upload Date", "Records", "Accuracy", "Amount", "Status"].map((header) => (
                  <TableHead key={header} className="font-semibold text-slate-700">
                    {header}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>

            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => <ReconSkeletonRow key={i} />)
              ) : reconciliations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-slate-400">
                    No reconciliations yet. Upload your first ISO file to get started.
                  </TableCell>
                </TableRow>
              ) : (
                reconciliations.map((recon, i) => (
                  <ReconDataRow key={recon.id} recon={recon} index={i} />
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
