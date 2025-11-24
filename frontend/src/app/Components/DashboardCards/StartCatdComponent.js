"use client";

import { motion } from "framer-motion";

export default function StatCard({ title, value, subtitle, icon: Icon, trend, trendUp }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="p-5 rounded-xl shadow-md bg-white border hover:shadow-lg transition"
    >
      <div className="flex items-start justify-between mb-3">

        {Icon && (
          <div className="p-2 rounded-lg bg-slate-100">
            <Icon className="w-5 h-5 text-slate-700" />
          </div>
        )}

        {trend && (
          <div className={`text-sm font-medium flex items-center gap-1
            ${trendUp ? "text-emerald-600" : "text-red-600"}`}>
            <span>{trendUp ? "↑" : "↓"}</span>
            <span>{trend}</span>
          </div>
        )}
      </div>

      <p className="text-sm text-slate-500">{title}</p>
      <h3 className="text-2xl font-bold text-slate-800">{value}</h3>

      {subtitle && <p className="text-xs text-slate-400 mt-">{subtitle}</p>}
    </motion.div>
  );
}
