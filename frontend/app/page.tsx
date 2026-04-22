import { DashboardShell } from "@/components/layout/DashboardShell";
import { HealthScoreSection } from "@/components/sections/HealthScoreSection";
import { ActionCardsSection } from "@/components/sections/ActionCardsSection";
import { LocalRadarSection } from "@/components/sections/LocalRadarSection";
import { RecentActivitySection } from "@/components/sections/RecentActivitySection";

export default function DashboardPage() {
  return (
    <DashboardShell>
      <div className="space-y-8">
        {/* Health Score Overview */}
        <HealthScoreSection />
        
        {/* AI Action Cards */}
        <ActionCardsSection />
        
        {/* Local Radar & Map */}
        <LocalRadarSection />
        
        {/* Recent Activity */}
        <RecentActivitySection />
      </div>
    </DashboardShell>
  );
}
