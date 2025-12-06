import StatCard from "../DashboardCards/StartCatdComponent";
import { FileText, TrendingUp, Coins, AlertTriangle } from "lucide-react";
import UploadFileButton from "./UploadFileComponent";
import ReconciliationsTable from "../Reconcilliation_Components/reconcilliation_table";
import PanzarActivityFeed from "../Panzar_Components/page";
import ReconciliationFiles from "../Reconcilliation_Components/get_all_reconcillation_files";
import UploadPage from "./uploadFile";

export default function DashboardPage() {
  

  const stats = {
    totalReconciliations: 12,
    averageAccuracy: 97,
    totalMinted: 25000,
    alerts: 2
  };

  return (
    <div >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

        <StatCard
          title="Total Reconciliations"
          value={stats.totalReconciliations}
          subtitle="All time"
          icon={FileText}
          trend="+12%"
          trendUp={true}
        />

        <StatCard
          title="Average Accuracy"
          value={`${stats.averageAccuracy}%`}
          subtitle="Across all files"
          icon={TrendingUp}
          trend="+2.3%"
          trendUp={true}
        />

        <StatCard
          title="Total Minted"
          value={`$${stats.totalMinted.toLocaleString()}`}
          subtitle="PANZAR stablecoin"
          icon={Coins}
          trend="+8.5%"
          trendUp={true}
        />

        <StatCard
          title="Active Alerts"
          value={stats.alerts}
          subtitle="Require attention"
          icon={AlertTriangle}
          trend={stats.alerts > 0 ? "! High" : "Good"}
          trendUp={stats.alerts === 0}
        />

      </div>
      
      {/* <div className="mt-5">
        <UploadFileButton />
      </div> */}
      
<div className="mt-5">
        {/* ✅ Render UploadPage instead of UploadFileButton */}
        <UploadPage />
      </div>


            
      <div className="mt-5 ">
        {/* <ReconciliationsTable /> */}
        <ReconciliationFiles/>
      </div>

        <div className="mt-5 ">
        <PanzarActivityFeed />
      </div>


{/*  */}

    </div>
  );
}
