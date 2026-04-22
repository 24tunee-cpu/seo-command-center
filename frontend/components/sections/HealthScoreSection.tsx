"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, AlertCircle, CheckCircle2, Globe } from "lucide-react";
import { HealthScoreGauge, HealthScoreBreakdown } from "@/components/charts/HealthScoreGauge";
import type { HealthScoreResponse } from "@/types";

// Mock data - would come from API
const mockHealthData: HealthScoreResponse = {
  health_score: 87,
  category: "good",
  breakdown: {
    core_web_vitals: 82,
    on_page_seo: 94,
    technical: 76,
    content: 88,
  },
  pages_analyzed: 156,
  total_issues: 23,
};

export function HealthScoreSection() {
  const [data, setData] = useState<HealthScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    const timer = setTimeout(() => {
      setData(mockHealthData);
      setLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-6 animate-pulse">
        <div className="h-48 bg-white/5 rounded-xl" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 lg:grid-cols-3 gap-6"
    >
      {/* Main Health Score Gauge */}
      <div className="lg:col-span-1 glass-card rounded-2xl p-6 flex flex-col items-center">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-cyber-400" />
          <h2 className="text-lg font-semibold text-foreground">Health Score</h2>
        </div>
        <HealthScoreGauge score={data.health_score} size={200} />
        <div className="mt-4 text-center">
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Globe className="w-4 h-4" />
            <span>{data.pages_analyzed} pages analyzed</span>
          </div>
        </div>
      </div>

      {/* Breakdown */}
      <div className="lg:col-span-1 glass-card rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-foreground mb-6">Score Breakdown</h2>
        <HealthScoreBreakdown score={data.health_score} breakdown={data.breakdown} />
      </div>

      {/* Issues Summary */}
      <div className="lg:col-span-1 glass-card rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-foreground mb-6">Issues Summary</h2>
        <div className="space-y-4">
          <IssueItem
            severity="critical"
            count={2}
            label="Critical Issues"
            icon={AlertCircle}
            color="text-red-400"
          />
          <IssueItem
            severity="high"
            count={5}
            label="High Priority"
            icon={AlertCircle}
            color="text-orange-400"
          />
          <IssueItem
            severity="medium"
            count={8}
            label="Medium Priority"
            icon={AlertCircle}
            color="text-amber-400"
          />
          <IssueItem
            severity="low"
            count={8}
            label="Low Priority"
            icon={CheckCircle2}
            color="text-green-400"
          />
        </div>
        <div className="mt-6 pt-6 border-t border-white/10">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Total Issues</span>
            <span className="text-2xl font-bold text-foreground">{data.total_issues}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function IssueItem({
  severity,
  count,
  label,
  icon: Icon,
  color,
}: {
  severity: string;
  count: number;
  label: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Icon className={`w-5 h-5 ${color}`} />
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <span className={`text-sm font-semibold ${color}`}>{count}</span>
    </div>
  );
}
