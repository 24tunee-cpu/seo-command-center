"use client";

import { motion } from "framer-motion";
import { cn, getHealthScoreColor, getHealthScoreGlow, calculateGaugeOffset } from "@/lib/utils";

interface HealthScoreGaugeProps {
  score: number;
  size?: number;
  showLabel?: boolean;
  animate?: boolean;
}

export function HealthScoreGauge({
  score,
  size = 180,
  showLabel = true,
  animate = true,
}: HealthScoreGaugeProps) {
  const radius = 54;
  const strokeWidth = 8;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const halfCircumference = circumference / 2;
  
  const offset = calculateGaugeOffset(score);
  const colorClass = getHealthScoreColor(score);
  const glowClass = getHealthScoreGlow(score);
  
  // Determine status text
  const getStatusText = (s: number) => {
    if (s >= 90) return "Excellent";
    if (s >= 70) return "Good";
    if (s >= 50) return "Needs Work";
    return "Poor";
  };

  // Get stroke color based on score
  const getStrokeColor = (s: number) => {
    if (s >= 90) return "#10b981"; // emerald-500
    if (s >= 70) return "#3b82f6"; // blue-500
    if (s >= 50) return "#f59e0b"; // amber-500
    return "#ef4444"; // red-500
  };

  return (
    <div
      className={cn("relative inline-flex items-center justify-center", glowClass)}
      style={{ width: size, height: size * 0.65 }}
    >
      <svg
        width={size}
        height={size * 0.65}
        viewBox={`0 0 ${radius * 2 + 20} ${radius + 20}`}
        className="transform -rotate-90"
      >
        {/* Background arc */}
        <circle
          cx={radius + 10}
          cy={radius + 10}
          r={normalizedRadius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${halfCircumference} ${circumference}`}
        />
        
        {/* Progress arc */}
        <motion.circle
          cx={radius + 10}
          cy={radius + 10}
          r={normalizedRadius}
          fill="none"
          stroke={getStrokeColor(score)}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${halfCircumference} ${circumference}`}
          initial={{ strokeDashoffset: halfCircumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ 
            duration: animate ? 1.5 : 0, 
            ease: "easeOut",
            delay: 0.2 
          }}
          style={{
            filter: `drop-shadow(0 0 10px ${getStrokeColor(score)}80)`,
          }}
        />
        
        {/* Gradient definitions */}
        <defs>
          <linearGradient id="gaugeGradient-excellent" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
          <linearGradient id="gaugeGradient-good" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#60a5fa" />
          </linearGradient>
          <linearGradient id="gaugeGradient-warning" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#fbbf24" />
          </linearGradient>
          <linearGradient id="gaugeGradient-poor" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="100%" stopColor="#f87171" />
          </linearGradient>
        </defs>
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-8">
        <motion.span
          className={cn("text-5xl font-bold tracking-tight", colorClass)}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          {Math.round(score)}
        </motion.span>
        
        {showLabel && (
          <motion.span
            className="text-sm font-medium text-muted-foreground mt-1"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            {getStatusText(score)}
          </motion.span>
        )}
      </div>

      {/* Tick marks */}
      <div className="absolute inset-0">
        {[0, 25, 50, 75, 100].map((tick) => {
          const angle = (tick / 100) * 180 - 180;
          const rad = (angle * Math.PI) / 180;
          const x1 = (radius + 10) + (normalizedRadius - 5) * Math.cos(rad);
          const y1 = (radius + 10) + (normalizedRadius - 5) * Math.sin(rad);
          const x2 = (radius + 10) + (normalizedRadius + 5) * Math.cos(rad);
          const y2 = (radius + 10) + (normalizedRadius + 5) * Math.sin(rad);

          return (
            <line
              key={tick}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="rgba(255, 255, 255, 0.3)"
              strokeWidth={2}
              className="absolute"
              style={{
                transform: `translate(${(size - (radius * 2 + 20)) / 2}px, ${(size * 0.65 - (radius + 20)) / 2}px)`,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

interface HealthScoreMiniProps {
  score: number;
  size?: number;
}

export function HealthScoreMini({ score, size = 48 }: HealthScoreMiniProps) {
  const colorClass = getHealthScoreColor(score);
  const glowClass = getHealthScoreGlow(score);
  
  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-full",
        "bg-white/5 border border-white/10",
        glowClass
      )}
      style={{ width: size, height: size }}
    >
      <span className={cn("text-lg font-bold", colorClass)}>{Math.round(score)}</span>
    </div>
  );
}

interface HealthScoreBreakdownProps {
  score: number;
  breakdown: {
    core_web_vitals: number;
    on_page_seo: number;
    technical: number;
    content: number;
  };
}

export function HealthScoreBreakdown({ score, breakdown }: HealthScoreBreakdownProps) {
  const items = [
    { label: "Core Web Vitals", value: breakdown.core_web_vitals, weight: 30 },
    { label: "On-Page SEO", value: breakdown.on_page_seo, weight: 25 },
    { label: "Technical", value: breakdown.technical, weight: 25 },
    { label: "Content", value: breakdown.content, weight: 20 },
  ];

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label} className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{item.label}</span>
            <div className="flex items-center gap-2">
              <span className={cn("font-medium", getHealthScoreColor(item.value))}>
                {Math.round(item.value)}
              </span>
              <span className="text-xs text-muted-foreground">({item.weight}%)</span>
            </div>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              className={cn(
                "h-full rounded-full",
                item.value >= 90 ? "bg-health-excellent" :
                item.value >= 70 ? "bg-health-good" :
                item.value >= 50 ? "bg-health-warning" : "bg-health-poor"
              )}
              initial={{ width: 0 }}
              animate={{ width: `${item.value}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
