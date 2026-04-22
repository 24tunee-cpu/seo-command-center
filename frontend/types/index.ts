/**
 * TypeScript type definitions for SEO Command Center
 */

// Project Types
export interface Project {
  id: string;
  name: string;
  domain: string;
  user_id: string;
  target_keywords: string[];
  target_locations: LocationPoint[];
  competitors: string[];
  health_score: number;
  health_category: 'excellent' | 'good' | 'needs_work' | 'poor';
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface LocationPoint {
  name: string;
  lat: number;
  lng: number;
  radius_m: number;
}

// Health Score Types
export interface HealthScoreBreakdown {
  core_web_vitals: number;
  on_page_seo: number;
  technical: number;
  content: number;
}

export interface HealthScoreResponse {
  health_score: number;
  category: 'excellent' | 'good' | 'needs_work' | 'poor';
  breakdown: HealthScoreBreakdown;
  pages_analyzed: number;
  total_issues: number;
}

// AI Action Card Types
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type Impact = 'high' | 'medium' | 'low';
export type Effort = 'high' | 'medium' | 'low';
export type CardStatus = 'pending' | 'swiped_left' | 'swiped_right' | 'completed' | 'dismissed';

export interface AIActionCard {
  id: string;
  card_id: string;
  title: string;
  description: string;
  category: 'technical' | 'content' | 'local' | 'competitor';
  severity: Severity;
  estimated_impact: Impact;
  estimated_effort: Effort;
  potential_traffic_gain?: number;
  affected_urls: string[];
  related_keywords: string[];
  status: CardStatus;
  dismissed_at?: string;
  completed_at?: string;
  user_notes?: string;
  created_at: string;
  expires_at?: string;
}

// Local Radar Types
export interface LocalRanking {
  id: string;
  keyword: string;
  location_name: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  map_pack_rank?: number;
  map_pack_present: boolean;
  organic_rank?: number;
  gmb_rating?: number;
  gmb_review_count?: number;
  distance_km?: number;
  scanned_at: string;
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  rank: number;
  location_name?: string;
  intensity: number;
}

export interface HeatmapData {
  keyword: string;
  total_points: number;
  average_rank?: number;
  top_3_count: number;
  top_10_count: number;
  heatmap_data: HeatmapPoint[];
}

// Crawl Audit Types
export interface CrawlAudit {
  id: string;
  url: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  status_code?: number;
  title?: string;
  title_length?: number;
  meta_description?: string;
  core_web_vitals_score?: number;
  issue_counts: Record<string, number>;
  word_count?: number;
  crawled_at: string;
}

// ROI Prediction Types
export interface ROIPrediction {
  id: string;
  keyword: string;
  search_volume: number;
  keyword_difficulty: number;
  current_position?: number;
  target_position: number;
  estimated_ctr_current?: number;
  estimated_ctr_target: number;
  predicted_monthly_clicks: number;
  predicted_monthly_conversions: number;
  predicted_monthly_revenue: number;
  estimated_monthly_value: number;
  roi_percentage: number;
  payback_months?: number;
  calculated_at: string;
}

// Competitor Types
export interface CompetitorSnapshot {
  id: string;
  competitor_domain: string;
  keyword: string;
  position: number;
  previous_position?: number;
  position_change: number;
  page_title?: string;
  page_url: string;
  content_changed: boolean;
  captured_at: string;
}

// Content Gap Types
export interface LSIKeyword {
  keyword: string;
  relevance_score: number;
  competitor_usage: string;
  frequency_in_competitors: number;
}

export interface ContentGapAnalysis {
  id: string;
  target_keyword: string;
  missing_lsi_keywords: LSIKeyword[];
  topic_clusters: TopicCluster[];
  entities_present: string[];
  suggested_word_count: number;
  suggested_headings: string[];
  analyzed_at: string;
}

export interface TopicCluster {
  topic: string;
  related_terms: Array<{ term: string; frequency: number }>;
  present_in_target: boolean;
  frequency: number;
}

// Backlink Types
export interface BacklinkProfile {
  id: string;
  referring_domain: string;
  referring_page: string;
  target_page: string;
  anchor_text: string;
  toxic_score: number;
  is_suspicious: boolean;
  suspicion_reasons: string[];
  disavow_recommended: boolean;
  disavowed: boolean;
  discovered_at: string;
}

// Chart Data Types
export interface TimeSeriesData {
  date: string;
  value: number;
  label?: string;
}

export interface RankTrendData {
  date: string;
  avg_map_rank?: number;
  avg_organic_rank?: number;
  scan_count: number;
}
