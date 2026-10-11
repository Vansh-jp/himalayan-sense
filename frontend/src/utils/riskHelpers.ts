export type RiskLevel = 'green' | 'yellow' | 'orange' | 'red';

export interface RiskStyle {
  hex: string;
  bg: string;
  text: string;
  label: string;
}

export const RISK_COLOR_MAP: Record<RiskLevel, RiskStyle> = {
  green: {
    hex: '#22c55e',
    bg: 'bg-green-100 dark:bg-green-950/40',
    text: 'text-green-800 dark:text-green-300',
    label: 'Low Risk'
  },
  yellow: {
    hex: '#eab308',
    bg: 'bg-yellow-100 dark:bg-yellow-950/40',
    text: 'text-yellow-800 dark:text-yellow-300',
    label: 'Moderate Risk'
  },
  orange: {
    hex: '#f97316',
    bg: 'bg-orange-100 dark:bg-orange-950/40',
    text: 'text-orange-800 dark:text-orange-300',
    label: 'High Risk'
  },
  red: {
    hex: '#ef4444',
    bg: 'bg-red-100 dark:bg-red-950/40',
    text: 'text-red-800 dark:text-red-300',
    label: 'Severe Risk'
  }
};