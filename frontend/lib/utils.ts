import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility to merge Tailwind classes with proper precedence
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as a percentage
 */
export function formatPercentage(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format currency value
 */
export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format large numbers with K/M suffixes
 */
export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
}

/**
 * Get color class based on health score
 */
export function getHealthScoreColor(score: number): string {
  if (score >= 90) return 'text-health-excellent';
  if (score >= 70) return 'text-health-good';
  if (score >= 50) return 'text-health-warning';
  return 'text-health-poor';
}

/**
 * Get glow class based on health score
 */
export function getHealthScoreGlow(score: number): string {
  if (score >= 90) return 'health-score-glow-excellent';
  if (score >= 70) return 'health-score-glow-good';
  if (score >= 50) return 'health-score-glow-warning';
  return 'health-score-glow-poor';
}

/**
 * Get color for severity level
 */
export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'bg-severity-critical',
    high: 'bg-severity-high',
    medium: 'bg-severity-medium',
    low: 'bg-severity-low',
    info: 'bg-severity-info',
  };
  return colors[severity] || colors.info;
}

/**
 * Truncate text with ellipsis
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength)}...`;
}

/**
 * Calculate gauge stroke offset for SVG
 */
export function calculateGaugeOffset(percentage: number): number {
  // Full circle circumference = 2 * PI * 54 ≈ 339.292
  // We use half circle, so effective circumference = 169.646
  const fullArc = 169.646;
  return fullArc - (percentage / 100) * fullArc;
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  const intervals = [
    { label: 'year', seconds: 31536000 },
    { label: 'month', seconds: 2592000 },
    { label: 'day', seconds: 86400 },
    { label: 'hour', seconds: 3600 },
    { label: 'minute', seconds: 60 },
  ];

  for (const interval of intervals) {
    const count = Math.floor(diffInSeconds / interval.seconds);
    if (count > 0) {
      return `${count} ${interval.label}${count > 1 ? 's' : ''} ago`;
    }
  }

  return 'just now';
}
