/**
 * API client for SEO Command Center backend
 */

import type {
  Project,
  HealthScoreResponse,
  AIActionCard,
  LocalRanking,
  HeatmapData,
  CrawlAudit,
  ROIPrediction,
  ContentGapAnalysis,
  CompetitorSnapshot,
  BacklinkProfile,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ==================== PROJECTS ====================

export async function getProjects(userId: string): Promise<Project[]> {
  return fetchAPI(`/projects/?user_id=${userId}`);
}

export async function getProject(projectId: string): Promise<Project> {
  return fetchAPI(`/projects/${projectId}`);
}

export async function createProject(data: Partial<Project>): Promise<Project> {
  return fetchAPI('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ==================== HEALTH SCORE ====================

export async function getHealthScore(projectId: string): Promise<HealthScoreResponse> {
  return fetchAPI(`/crawler/health-score/${projectId}`);
}

// ==================== AI ACTION CARDS ====================

export async function getActionCards(
  projectId: string,
  options?: { status?: string; severity?: string }
): Promise<AIActionCard[]> {
  const params = new URLSearchParams();
  if (options?.status) params.append('status', options.status);
  if (options?.severity) params.append('severity', options.severity);
  
  return fetchAPI(`/projects/${projectId}/action-cards?${params.toString()}`);
}

export async function swipeActionCard(
  projectId: string,
  cardId: string,
  direction: 'left' | 'right' | 'complete'
): Promise<void> {
  return fetchAPI(`/projects/${projectId}/action-cards/${cardId}/swipe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `direction=${direction}`,
  });
}

// ==================== LOCAL RADAR ====================

export async function scanLocalRankings(
  projectId: string,
  keyword: string,
  locations: Array<{ name: string; lat: number; lng: number; radius_m: number }>
): Promise<LocalRanking[]> {
  return fetchAPI('/local-radar/scan', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId, keyword, locations }),
  });
}

export async function getHeatmapData(
  projectId: string,
  keyword: string,
  days = 7
): Promise<HeatmapData> {
  return fetchAPI(`/local-radar/heatmap-data/${projectId}?keyword=${keyword}&days=${days}`);
}

export async function getRankingTrends(
  projectId: string,
  keyword: string,
  days = 30
): Promise<{ trend_data: Array<{ date: string; avg_map_rank?: number; avg_organic_rank?: number }> }> {
  return fetchAPI(`/local-radar/ranking-trends/${projectId}?keyword=${keyword}&days=${days}`);
}

// ==================== CRAWLER ====================

export async function auditUrl(
  projectId: string,
  url: string,
  checkPagespeed = true
): Promise<CrawlAudit> {
  return fetchAPI('/crawler/audit-url', {
    method: 'POST',
    body: JSON.stringify({
      url,
      project_id: projectId,
      check_pagespeed: checkPagespeed,
    }),
  });
}

export async function getProjectAudits(projectId: string): Promise<CrawlAudit[]> {
  return fetchAPI(`/crawler/audits/${projectId}`);
}

// ==================== ROI PREDICTOR ====================

export async function calculateROI(data: {
  project_id: string;
  keyword: string;
  search_volume: number;
  keyword_difficulty: number;
  current_position?: number;
  target_position: number;
  conversion_rate?: number;
  average_order_value?: number;
}): Promise<ROIPrediction> {
  return fetchAPI('/roi/calculate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getROIPredictions(
  projectId: string,
  minROI?: number
): Promise<ROIPrediction[]> {
  const params = minROI ? `?min_roi=${minROI}` : '';
  return fetchAPI(`/roi/predictions/${projectId}${params}`);
}

export async function getTopOpportunities(projectId: string): Promise<{
  opportunities: Array<{
    keyword: string;
    roi_percentage: number;
    monthly_value: number;
    keyword_difficulty: number;
    target_position: number;
  }>;
}> {
  return fetchAPI(`/roi/top-opportunities/${projectId}`);
}

// ==================== CONTENT GAP ====================

export async function analyzeContentGap(data: {
  project_id: string;
  target_keyword: string;
  target_url: string;
  competitor_urls: string[];
}): Promise<ContentGapAnalysis> {
  return fetchAPI('/content-gap/analyze', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getContentGapAnalyses(projectId: string): Promise<ContentGapAnalysis[]> {
  return fetchAPI(`/content-gap/analyses/${projectId}`);
}

// ==================== COMPETITOR INTEL ====================

export async function getCompetitorSnapshots(
  projectId: string,
  options?: { competitor?: string; days?: number }
): Promise<CompetitorSnapshot[]> {
  const params = new URLSearchParams();
  if (options?.competitor) params.append('competitor', options.competitor);
  if (options?.days) params.append('days', options.days.toString());
  
  return fetchAPI(`/competitors/snapshots/${projectId}?${params.toString()}`);
}

export async function getCompetitorChanges(
  projectId: string,
  hours = 24
): Promise<{
  period_hours: number;
  content_changes: number;
  ranking_changes: number;
  details: unknown;
}> {
  return fetchAPI(`/competitors/changes/${projectId}?hours=${hours}`);
}

// ==================== BACKLINK ANALYZER ====================

export async function getBacklinkProfile(
  projectId: string,
  toxicOnly = false
): Promise<BacklinkProfile[]> {
  return fetchAPI(`/backlinks/profile/${projectId}?toxic_only=${toxicOnly}`);
}

export async function generateDisavowList(projectId: string): Promise<{
  total_domains: number;
  disavow_format: string;
  domains: string[];
}> {
  return fetchAPI(`/backlinks/disavow-list/${projectId}`);
}
