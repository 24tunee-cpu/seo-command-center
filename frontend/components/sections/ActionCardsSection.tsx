"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Filter } from "lucide-react";
import { AIActionCardStack } from "@/components/cards/AIActionCard";
import type { AIActionCard } from "@/types";

// Mock data - would come from API
const mockActionCards: AIActionCard[] = [
  {
    id: "1",
    card_id: "card-001",
    title: "Fix Missing Alt Text on Product Images",
    description: "24 product images are missing alt text, impacting accessibility and image SEO rankings. Adding descriptive alt text can improve your image search visibility.",
    category: "technical",
    severity: "high",
    estimated_impact: "high",
    estimated_effort: "low",
    potential_traffic_gain: 450,
    affected_urls: ["/products/item-1", "/products/item-2", "/products/item-3"],
    related_keywords: ["image seo", "alt text", "accessibility"],
    status: "pending",
    created_at: new Date().toISOString(),
  },
  {
    id: "2",
    card_id: "card-002",
    title: "Add Local Schema Markup to Contact Page",
    description: "Your contact page is missing LocalBusiness schema markup. Adding structured data can help you appear in local pack results and improve click-through rates.",
    category: "local",
    severity: "medium",
    estimated_impact: "high",
    estimated_effort: "low",
    potential_traffic_gain: 320,
    affected_urls: ["/contact"],
    related_keywords: ["local seo", "schema markup", "structured data"],
    status: "pending",
    created_at: new Date().toISOString(),
  },
  {
    id: "3",
    card_id: "card-003",
    title: "Improve Page Speed on Mobile",
    description: "Core Web Vitals report shows LCP of 3.2s on mobile. Optimizing images and reducing JavaScript can improve your mobile ranking factor.",
    category: "technical",
    severity: "critical",
    estimated_impact: "high",
    estimated_effort: "high",
    potential_traffic_gain: 890,
    affected_urls: ["/", "/about", "/services"],
    related_keywords: ["core web vitals", "page speed", "mobile optimization"],
    status: "pending",
    created_at: new Date().toISOString(),
  },
  {
    id: "4",
    card_id: "card-004",
    title: "Target Missing LSI Keywords in Blog Content",
    description: "Competitor analysis shows you're missing key semantic terms: 'digital marketing strategy', 'ROI optimization', and 'conversion tracking'.",
    category: "content",
    severity: "medium",
    estimated_impact: "medium",
    estimated_effort: "medium",
    potential_traffic_gain: 180,
    affected_urls: ["/blog/marketing-tips", "/blog/seo-guide"],
    related_keywords: ["content gap", "lsi keywords", "semantic seo"],
    status: "pending",
    created_at: new Date().toISOString(),
  },
];

export function ActionCardsSection() {
  const [cards, setCards] = useState<AIActionCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setCards(mockActionCards);
      setLoading(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const handleCardsEmpty = () => {
    console.log("All cards reviewed");
  };

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-cyber-400" />
          <h2 className="text-lg font-semibold text-foreground">AI Recommendations</h2>
        </div>
        <div className="h-[400px] flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-2 border-cyber-400 border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="glass-card rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-cyber-400/20 to-purple-500/20">
            <Sparkles className="w-5 h-5 text-cyber-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">AI Action Cards</h2>
            <p className="text-sm text-muted-foreground">
              Swipe right to accept, left to dismiss
            </p>
          </div>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm">
          <Filter className="w-4 h-4" />
          Filter
        </button>
      </div>

      <AIActionCardStack cards={cards} onCardsEmpty={handleCardsEmpty} />
    </motion.div>
  );
}
