"use client";

import { motion } from "framer-motion";
import { Clock, CheckCircle2, AlertCircle, FileSearch, Globe, TrendingUp } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

const recentActivities = [
  {
    id: 1,
    type: "crawl",
    message: "Technical crawl completed for 156 pages",
    details: "23 issues found, 3 critical",
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    icon: FileSearch,
    color: "text-cyber-400",
  },
  {
    id: 2,
    type: "local",
    message: "Local radar scan completed",
    details: "25 grid points analyzed for 'digital marketing agency'",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    icon: Globe,
    color: "text-emerald-400",
  },
  {
    id: 3,
    type: "roi",
    message: "ROI calculation updated",
    details: "Top opportunity: +$2,450/month potential value",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
    icon: TrendingUp,
    color: "text-amber-400",
  },
  {
    id: 4,
    type: "fix",
    message: "Critical issue resolved",
    details: "Missing H1 tags fixed on 12 pages",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    icon: CheckCircle2,
    color: "text-green-400",
  },
  {
    id: 5,
    type: "alert",
    message: "Competitor ranking change detected",
    details: "competitor-x.com gained 3 positions for 'seo services'",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString(),
    icon: AlertCircle,
    color: "text-red-400",
  },
];

export function RecentActivitySection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="glass-card rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-white/5">
            <Clock className="w-5 h-5 text-cyber-300" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">Recent Activity</h2>
        </div>
        <button className="text-sm text-cyber-400 hover:text-cyber-300 transition-colors">
          View All
        </button>
      </div>

      <div className="space-y-4">
        {recentActivities.map((activity, index) => (
          <motion.div
            key={activity.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * index }}
            className="flex items-start gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/[0.07] transition-colors"
          >
            <div className={`p-2 rounded-lg bg-white/5 ${activity.color}`}>
              <activity.icon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground">{activity.message}</p>
              <p className="text-xs text-muted-foreground mt-1">{activity.details}</p>
            </div>
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {formatRelativeTime(activity.timestamp)}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
