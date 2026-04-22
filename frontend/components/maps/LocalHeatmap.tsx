"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { motion } from "framer-motion";
import { MapPin, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { HeatmapPoint } from "@/types";
import "leaflet/dist/leaflet.css";

interface LocalHeatmapProps {
  center: { lat: number; lng: number };
  data: HeatmapPoint[];
  zoom?: number;
}

// Map bounds fitter component
function MapBoundsFitter({ points }: { points: HeatmapPoint[] }) {
  const map = useMap();
  
  useEffect(() => {
    if (points.length > 0) {
      const bounds = points.map((p) => [p.lat, p.lng] as [number, number]);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, points]);
  
  return null;
}

export function LocalHeatmap({ center, data, zoom = 13 }: LocalHeatmapProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const getRankColor = (rank: number): string => {
    if (rank <= 3) return "#10b981"; // Green - excellent
    if (rank <= 5) return "#3b82f6"; // Blue - good
    if (rank <= 10) return "#f59e0b"; // Amber - needs work
    return "#ef4444"; // Red - poor
  };

  const getRankRadius = (intensity: number): number => {
    return 8 + intensity * 12;
  };

  if (!mounted) {
    return (
      <div className="w-full h-[400px] rounded-xl bg-card animate-pulse flex items-center justify-center">
        <span className="text-muted-foreground">Loading map...</span>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[400px] rounded-xl overflow-hidden">
      <MapContainer
        center={[center.lat, center.lng]}
        zoom={zoom}
        scrollWheelZoom={false}
        className="w-full h-full"
        style={{ background: "hsl(222 47% 6%)" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapBoundsFitter points={data} />

        {data.map((point, index) => (
          <CircleMarker
            key={index}
            center={[point.lat, point.lng]}
            radius={getRankRadius(point.intensity)}
            fillColor={getRankColor(point.rank)}
            color={getRankColor(point.rank)}
            weight={2}
            opacity={0.8}
            fillOpacity={0.6}
          >
            <Popup>
              <div className="p-2 min-w-[200px]">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-foreground">
                    {point.location_name || "Unknown Location"}
                  </span>
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-xs font-bold",
                      point.rank <= 3
                        ? "bg-emerald-500/20 text-emerald-400"
                        : point.rank <= 10
                        ? "bg-amber-500/20 text-amber-400"
                        : "bg-red-500/20 text-red-400"
                    )}
                  >
                    #{point.rank}
                  </span>
                </div>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-3 h-3" />
                    <span>
                      {point.lat.toFixed(4)}, {point.lng.toFixed(4)}
                    </span>
                  </div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Legend overlay */}
      <div className="absolute bottom-4 right-4 glass-card p-4 rounded-xl">
        <h4 className="text-sm font-medium text-foreground mb-3">Ranking Legend</h4>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#10b981]" />
            <span className="text-xs text-muted-foreground">Rank 1-3 (Excellent)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#3b82f6]" />
            <span className="text-xs text-muted-foreground">Rank 4-5 (Good)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#f59e0b]" />
            <span className="text-xs text-muted-foreground">Rank 6-10 (Needs Work)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
            <span className="text-xs text-muted-foreground">Rank 11+ (Poor)</span>
          </div>
        </div>
      </div>

      {/* Stats overlay */}
      <div className="absolute top-4 left-4 glass-card p-4 rounded-xl">
        <div className="flex items-center gap-4">
          <div>
            <div className="flex items-center gap-1 text-emerald-400">
              <TrendingUp className="w-4 h-4" />
              <span className="text-lg font-bold">
                {data.filter((d) => d.rank <= 3).length}
              </span>
            </div>
            <span className="text-xs text-muted-foreground">Top 3</span>
          </div>
          <div className="w-px h-8 bg-white/10" />
          <div>
            <div className="flex items-center gap-1 text-amber-400">
              <TrendingDown className="w-4 h-4" />
              <span className="text-lg font-bold">
                {data.filter((d) => d.rank > 10).length}
              </span>
            </div>
            <span className="text-xs text-muted-foreground">Rank 10+</span>
          </div>
          <div className="w-px h-8 bg-white/10" />
          <div>
            <div className="text-lg font-bold text-foreground">
              {data.length}
            </div>
            <span className="text-xs text-muted-foreground">Total Points</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Simple heatmap grid view for when map is not needed
interface HeatmapGridProps {
  data: HeatmapPoint[];
  gridSize?: number;
}

export function HeatmapGrid({ data, gridSize = 5 }: HeatmapGridProps) {
  // Organize data into grid
  const sorted = [...data].sort((a, b) => a.intensity - b.intensity);
  
  return (
    <div className="grid grid-cols-5 gap-2 p-4">
      {sorted.map((point, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: idx * 0.05 }}
          className={cn(
            "aspect-square rounded-lg flex items-center justify-center",
            "text-xs font-bold transition-all duration-300",
            point.rank <= 3
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : point.rank <= 5
              ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
              : point.rank <= 10
              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
              : "bg-red-500/20 text-red-400 border border-red-500/30"
          )}
          title={`Rank ${point.rank} at ${point.location_name}`}
        >
          {point.rank}
        </motion.div>
      ))}
    </div>
  );
}
