"use client";

import { useState, useRef } from "react";
import { motion, PanInfo, useMotionValue, useTransform } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  TrendingUp,
  X,
  Check,
  Zap,
  Globe,
  FileText,
  Users,
  ArrowRight,
} from "lucide-react";
import { cn, getSeverityColor } from "@/lib/utils";
import type { AIActionCard as AIActionCardType } from "@/types";

interface AIActionCardProps {
  card: AIActionCardType;
  onSwipe: (direction: "left" | "right", cardId: string) => void;
  onComplete: (cardId: string) => void;
}

const categoryIcons = {
  technical: Zap,
  content: FileText,
  local: Globe,
  competitor: Users,
};

const severityIcons = {
  critical: AlertTriangle,
  high: AlertTriangle,
  medium: Clock,
  low: CheckCircle2,
  info: CheckCircle2,
};

export function AIActionCard({ card, onSwipe, onComplete }: AIActionCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState<"left" | "right" | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-15, 15]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [1, 1, 1, 1, 1]);
  const background = useTransform(
    x,
    [-200, -100, 0, 100, 200],
    [
      "rgba(239, 68, 68, 0.2)",
      "rgba(239, 68, 68, 0.1)",
      "rgba(255, 255, 255, 0.05)",
      "rgba(16, 185, 129, 0.1)",
      "rgba(16, 185, 129, 0.2)",
    ]
  );

  const Icon = categoryIcons[card.category];
  const SeverityIcon = severityIcons[card.severity];

  const handleDragEnd = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    setIsDragging(false);
    
    if (info.offset.x > 100) {
      setSwipeDirection("right");
      setTimeout(() => onSwipe("right", card.card_id), 300);
    } else if (info.offset.x < -100) {
      setSwipeDirection("left");
      setTimeout(() => onSwipe("left", card.card_id), 300);
    }
  };

  const handleSwipeClick = (direction: "left" | "right") => {
    setSwipeDirection(direction);
    setTimeout(() => onSwipe(direction, card.card_id), 300);
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "high":
        return "text-health-excellent";
      case "medium":
        return "text-health-warning";
      default:
        return "text-muted-foreground";
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case "low":
        return "text-health-excellent";
      case "medium":
        return "text-health-warning";
      default:
        return "text-health-poor";
    }
  };

  return (
    <motion.div
      ref={cardRef}
      style={{ x, rotate, opacity, background }}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.8}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={handleDragEnd}
      animate={{
        x: swipeDirection === "left" ? -500 : swipeDirection === "right" ? 500 : 0,
        opacity: swipeDirection ? 0 : 1,
        rotate: swipeDirection === "left" ? -30 : swipeDirection === "right" ? 30 : 0,
      }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className={cn(
        "relative w-full max-w-md mx-auto rounded-2xl overflow-hidden",
        "glass-card cursor-grab active:cursor-grabbing",
        "select-none touch-pan-y"
      )}
    >
      {/* Swipe indicators */}
      <motion.div
        style={{ opacity: useTransform(x, [-200, -50, 0], [1, 0.5, 0]) }}
        className="absolute left-4 top-1/2 -translate-y-1/2 z-10"
      >
        <div className="bg-red-500/20 border-2 border-red-500 rounded-full p-3">
          <X className="w-8 h-8 text-red-500" />
        </div>
      </motion.div>
      
      <motion.div
        style={{ opacity: useTransform(x, [0, 50, 200], [0, 0.5, 1]) }}
        className="absolute right-4 top-1/2 -translate-y-1/2 z-10"
      >
        <div className="bg-green-500/20 border-2 border-green-500 rounded-full p-3">
          <Check className="w-8 h-8 text-green-500" />
        </div>
      </motion.div>

      {/* Card content */}
      <div className="p-6 relative z-0">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "w-12 h-12 rounded-xl flex items-center justify-center",
                "bg-gradient-to-br from-cyber-400/20 to-cyber-600/20",
                "border border-cyber-400/30"
              )}
            >
              <Icon className="w-6 h-6 text-cyber-300" />
            </div>
            <div>
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {card.category}
              </span>
              <h3 className="text-lg font-semibold text-foreground leading-tight">
                {card.title}
              </h3>
            </div>
          </div>
          
          <div
            className={cn(
              "flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium",
              getSeverityColor(card.severity),
              "bg-opacity-20"
            )}
          >
            <SeverityIcon className="w-3 h-3" />
            <span className="capitalize">{card.severity}</span>
          </div>
        </div>

        {/* Description */}
        <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
          {card.description}
        </p>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Impact</span>
            </div>
            <span className={cn("text-sm font-semibold capitalize", getImpactColor(card.estimated_impact))}>
              {card.estimated_impact}
            </span>
          </div>
          
          <div className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Effort</span>
            </div>
            <span className={cn("text-sm font-semibold capitalize", getEffortColor(card.estimated_effort))}>
              {card.estimated_effort}
            </span>
          </div>
        </div>

        {/* Traffic gain */}
        {card.potential_traffic_gain && (
          <div className="flex items-center gap-2 mb-4 p-3 bg-cyber-500/10 rounded-lg border border-cyber-500/20">
            <TrendingUp className="w-4 h-4 text-cyber-400" />
            <span className="text-sm text-cyber-100">
              Potential traffic gain: <strong>+{card.potential_traffic_gain.toLocaleString()}</strong> visits/month
            </span>
          </div>
        )}

        {/* Affected URLs */}
        {card.affected_urls.length > 0 && (
          <div className="mb-4">
            <span className="text-xs text-muted-foreground mb-2 block">
              Affected URLs ({card.affected_urls.length})
            </span>
            <div className="space-y-1">
              {card.affected_urls.slice(0, 3).map((url, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs text-muted-foreground truncate"
                >
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  <span className="truncate">{url}</span>
                </div>
              ))}
              {card.affected_urls.length > 3 && (
                <span className="text-xs text-muted-foreground">
                  +{card.affected_urls.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => handleSwipeClick("left")}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl
                     bg-white/5 hover:bg-red-500/20 text-muted-foreground hover:text-red-400
                     transition-colors duration-200 font-medium"
          >
            <X className="w-4 h-4" />
            Dismiss
          </button>
          
          <button
            onClick={() => handleSwipeClick("right")}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl
                     bg-cyber-500/20 hover:bg-cyber-500/30 text-cyber-100
                     border border-cyber-500/30 hover:border-cyber-500/50
                     transition-all duration-200 font-medium"
          >
            <span>Accept</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Complete button for accepted cards */}
        {card.status === "swiped_right" && (
          <button
            onClick={() => onComplete(card.card_id)}
            className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-3 rounded-xl
                     bg-health-excellent/20 hover:bg-health-excellent/30 text-health-excellent
                     border border-health-excellent/30 transition-all duration-200 font-medium"
          >
            <CheckCircle2 className="w-4 h-4" />
            Mark Complete
          </button>
        )}
      </div>

      {/* Drag hint */}
      {!isDragging && !swipeDirection && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-muted-foreground/50">
          Swipe to dismiss or accept
        </div>
      )}
    </motion.div>
  );
}

interface AIActionCardStackProps {
  cards: AIActionCardType[];
  onCardsEmpty: () => void;
}

export function AIActionCardStack({ cards, onCardsEmpty }: AIActionCardStackProps) {
  const [stack, setStack] = useState(cards);

  const handleSwipe = async (direction: "left" | "right", cardId: string) => {
    // Remove swiped card
    setStack((prev) => prev.filter((c) => c.card_id !== cardId));

    // TODO: Call API to update card status
    console.log(`Card ${cardId} swiped ${direction}`);

    if (stack.length <= 1) {
      onCardsEmpty();
    }
  };

  const handleComplete = async (cardId: string) => {
    setStack((prev) => prev.filter((c) => c.card_id !== cardId));
    
    // TODO: Call API to mark as complete
    console.log(`Card ${cardId} marked complete`);

    if (stack.length <= 1) {
      onCardsEmpty();
    }
  };

  if (stack.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <CheckCircle2 className="w-16 h-16 text-health-excellent/50 mb-4" />
        <h3 className="text-xl font-semibold text-foreground mb-2">All Caught Up!</h3>
        <p className="text-muted-foreground max-w-sm">
          You&apos;ve reviewed all AI recommendations. New suggestions will appear as we analyze your site.
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-[500px] flex items-center justify-center">
      {stack.slice(0, 3).map((card, index) => (
        <motion.div
          key={card.card_id}
          className="absolute w-full"
          style={{
            zIndex: stack.length - index,
            scale: 1 - index * 0.05,
            y: index * 10,
            opacity: 1 - index * 0.2,
          }}
          animate={{
            scale: 1 - index * 0.05,
            y: index * 10,
            opacity: index === 0 ? 1 : 0.6 - index * 0.2,
          }}
        >
          <AIActionCard
            card={card}
            onSwipe={handleSwipe}
            onComplete={handleComplete}
          />
        </motion.div>
      ))}
    </div>
  );
}
