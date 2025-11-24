"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Coins } from "lucide-react";
import { format } from "date-fns";
import { motion } from "framer-motion";

import ActivitySkeleton from "./ActivitySkeleton";
import { activityConfig } from "./activityConfig";
import StatusActivityBadge from "./StatusActivityBadge";

export default function PanzarActivityFeed({
  activities = [],
  isLoading = false,
}) {
  const hasActivities = Array.isArray(activities) && activities.length > 0;

  return (
    <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
      <CardHeader className="border-b border-slate-100 pb-4">
        <CardTitle className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Coins className="w-5 h-5 text-amber-600" />
          Recent PANZAR Activity
        </CardTitle>
      </CardHeader>

      <CardContent className="p-6">
        {isLoading ? (
          <ActivitySkeleton />
        ) : !hasActivities ? (
          <div className="text-center py-12 text-slate-400">
            No PANZAR activity yet. Start minting or burning tokens.
          </div>
        ) : (
          <div className="space-y-4">
            {activities.map((activity, index) => {
              const cfg = activityConfig[activity.activity_type] || {};
              const Icon = cfg.icon || Coins;

              return (
                <motion.div
                  key={activity.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center gap-4 p-4 rounded-xl hover:bg-slate-50 transition-colors border border-slate-100"
                >
                  {/* Icon */}
                  <div className={`p-3 rounded-full ${cfg.bg || "bg-slate-100"}`}>
                    <Icon className={`w-6 h-6 ${cfg.color || "text-slate-600"}`} />
                  </div>

                  {/* Main content */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold">{cfg.label || activity.activity_type}</span>
                      <span className="text-xl font-bold">
                        ${activity.amount?.toLocaleString()}
                      </span>
                    </div>

                    <div className="text-sm text-slate-500 flex gap-2">
                      <span>{format(new Date(activity.timestamp), "MMM d, yyyy HH:mm")}</span>
                      {activity.recipient && (
                        <>
                          <span>•</span>
                          <span className="truncate">{activity.recipient}</span>
                        </>
                      )}
                    </div>

                    {activity.reference_id && (
                      <div className="mt-1 text-xs text-slate-400 truncate">
                        {activity.reference_id}
                      </div>
                    )}
                  </div>

                  {/* Status */}
                  <StatusActivityBadge status={activity.status} />
                </motion.div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
