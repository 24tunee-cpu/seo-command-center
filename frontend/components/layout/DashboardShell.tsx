"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Globe,
  MapPin,
  Users,
  FileSearch,
  Link2,
  TrendingUp,
  Settings,
  Bell,
  Search,
  Menu,
  X,
  Command,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { HealthScoreMini } from "@/components/charts/HealthScoreGauge";

interface DashboardShellProps {
  children: React.ReactNode;
}

const navigation = [
  { name: "Overview", href: "#", icon: LayoutDashboard, current: true },
  { name: "Technical Crawler", href: "#", icon: FileSearch, current: false },
  { name: "Local Radar", href: "#", icon: MapPin, current: false },
  { name: "Competitors", href: "#", icon: Users, current: false },
  { name: "Content Gap", href: "#", icon: Globe, current: false },
  { name: "Backlinks", href: "#", icon: Link2, current: false },
  { name: "ROI Predictor", href: "#", icon: TrendingUp, current: false },
  { name: "Settings", href: "#", icon: Settings, current: false },
];

export function DashboardShell({ children }: DashboardShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const healthScore = 87; // Would come from API

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar */}
      <motion.div
        initial={{ x: -280 }}
        animate={{ x: sidebarOpen ? 0 : -280 }}
        className="fixed inset-y-0 left-0 z-50 w-72 bg-card border-r border-border lg:hidden"
      >
        <div className="flex h-16 items-center justify-between px-6 border-b border-border">
          <span className="text-xl font-bold bg-gradient-to-r from-cyber-400 to-blue-500 bg-clip-text text-transparent">
            SEO Command
          </span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 rounded-lg hover:bg-white/5"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <SidebarContent />
      </motion.div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-72 lg:flex-col">
        <div className="flex flex-col flex-1 min-h-0 bg-card border-r border-border">
          <div className="flex items-center h-16 px-6 border-b border-border">
            <Command className="w-8 h-8 text-cyber-400 mr-3" />
            <span className="text-xl font-bold bg-gradient-to-r from-cyber-400 to-blue-500 bg-clip-text text-transparent">
              SEO Command
            </span>
          </div>
          <SidebarContent />
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-72">
        {/* Top header */}
        <header className="sticky top-0 z-40 h-16 glass-panel border-b border-border">
          <div className="flex items-center justify-between h-full px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 -ml-2 rounded-lg hover:bg-white/5 lg:hidden"
              >
                <Menu className="w-5 h-5" />
              </button>

              {/* Search bar */}
              <div className="hidden sm:flex items-center flex-1 max-w-md">
                <div className="relative w-full">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search projects, keywords..."
                    className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 
                             text-sm text-foreground placeholder:text-muted-foreground
                             focus:outline-none focus:ring-2 focus:ring-cyber-500/50"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Project health mini */}
              <div className="hidden sm:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-white/5">
                <span className="text-sm text-muted-foreground">Health Score</span>
                <HealthScoreMini score={healthScore} size={32} />
              </div>

              {/* Notifications */}
              <button className="relative p-2 rounded-lg hover:bg-white/5">
                <Bell className="w-5 h-5 text-muted-foreground" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-cyber-400 rounded-full" />
              </button>

              {/* User avatar */}
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyber-400 to-blue-500" />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="py-8 px-4 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}

function SidebarContent() {
  return (
    <div className="flex-1 flex flex-col overflow-y-auto py-4">
      <nav className="flex-1 px-4 space-y-1">
        {navigation.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              item.current
                ? "bg-cyber-500/20 text-cyber-100 border border-cyber-500/30"
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
            )}
          >
            <item.icon className={cn("w-5 h-5", item.current && "text-cyber-400")} />
            {item.name}
          </a>
        ))}
      </nav>

      {/* Project selector */}
      <div className="px-4 mt-6">
        <div className="p-3 rounded-lg bg-white/5 border border-white/10">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Current Project</span>
          <div className="mt-1 flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyber-400" />
            <span className="text-sm font-medium text-foreground">example.com</span>
          </div>
        </div>
      </div>
    </div>
  );
}
