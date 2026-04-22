"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Target, TrendingUp } from "lucide-react";
import { LocalHeatmap } from "@/components/maps/LocalHeatmap";
import type { HeatmapData } from "@/types";

// Mock data - would come from API
const mockHeatmapData: HeatmapData = {
  keyword: "digital marketing agency",
  total_points: 25,
  average_rank: 4.2,
  top_3_count: 12,
  top_10_count: 20,
  heatmap_data: [
    { lat: 40.7128, lng: -74.006, rank: 2, location_name: "Downtown", intensity: 1 },
    { lat: 40.73, lng: -74.01, rank: 3, location_name: "Midtown", intensity: 0.9 },
    { lat: 40.72, lng: -73.99, rank: 1, location_name: "East Village", intensity: 1 },
    { lat: 40.74, lng: -74.02, rank: 5, location_name: "Chelsea", intensity: 0.7 },
    { lat: 40.71, lng: -74.015, rank: 7, location_name: "Financial District", intensity: 0.4 },
    { lat: 40.735, lng: -73.98, rank: 4, location_name: "Gramercy", intensity: 0.7 },
    { lat: 40.725, lng: -73.995, rank: 6, location_name: "Soho", intensity: 0.5 },
    { lat: 40.705, lng: -74.0, rank: 12, location_name: "Battery Park", intensity: 0.2 },
    { lat: 40.745, lng: -73.985, rank: 3, location_name: "Flatiron", intensity: 0.9 },
    { lat: 40.728, lng: -73.995, rank: 8, location_name: "Greenwich Village", intensity: 0.3 },
    { lat: 40.718, lng: -74.005, rank: 2, location_name: "Chinatown", intensity: 1 },
    { lat: 40.738, lng: -74.005, rank: 9, location_name: "Meatpacking", intensity: 0.3 },
    { lat: 40.722, lng: -73.985, rank: 1, location_name: "Lower East Side", intensity: 1 },
    { lat: 40.732, lng: -74.01, rank: 4, location_name: "Hell's Kitchen", intensity: 0.7 },
    { lat: 40.715, lng: -73.975, rank: 5, location_name: "Tribeca", intensity: 0.6 },
    { lat: 40.74, lng: -73.97, rank: 6, location_name: "Upper East Side", intensity: 0.5 },
    { lat: 40.775, lng: -73.97, rank: 11, location_name: "Central Park", intensity: 0.2 },
    { lat: 40.69, lng: -73.99, rank: 15, location_name: "Brooklyn Heights", intensity: 0.1 },
    { lat: 40.755, lng: -73.985, rank: 3, location_name: "Times Square", intensity: 0.9 },
    { lat: 40.748, lng: -73.985, rank: 2, location_name: "Empire State", intensity: 1 },
    { lat: 40.735, lng: -74.0, rank: 7, location_name: "West Village", intensity: 0.4 },
    { lat: 40.725, lng: -74.02, rank: 8, location_name: "West Chelsea", intensity: 0.3 },
    { lat: 40.745, lng: -74.0, rank: 5, location_name: "Hudson Yards", intensity: 0.6 },
    { lat: 40.715, lng: -74.01, rank: 4, location_name: "Wall Street", intensity: 0.7 },
    { lat: 40.73, lng: -73.985, rank: 3, location_name: "Union Square", intensity: 0.9 },
  ],
};

export function LocalRadarSection() {
  const [data, setData] = useState<HeatmapData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setData(mockHeatmapData);
      setLoading(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <MapPin className="w-5 h-5 text-cyber-400" />
          <h2 className="text-lg font-semibold text-foreground">Local Radar</h2>
        </div>
        <div className="h-[400px] flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-2 border-cyber-400 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="glass-card rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyber-500/20">
            <MapPin className="w-5 h-5 text-cyber-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Local Radar</h2>
            <p className="text-sm text-muted-foreground">
              Tracking: <span className="text-cyber-300">{data.keyword}</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <StatBadge
            icon={Target}
            label="Avg Rank"
            value={`#${data.average_rank?.toFixed(1)}`}
            color="text-cyber-300"
          />
          <StatBadge
            icon={TrendingUp}
            label="Top 3"
            value={`${data.top_3_count}/${data.total_points}`}
            color="text-emerald-400"
          />
        </div>
      </div>

      <LocalHeatmap
        center={{ lat: 40.7128, lng: -74.006 }}
        data={data.heatmap_data}
        zoom={13}
      />
    </motion.div>
  );
}

function StatBadge({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5">
      <Icon className={`w-4 h-4 ${color}`} />
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className={`text-sm font-semibold ${color}`}>{value}</span>
      </div>
    </div>
  );
}
