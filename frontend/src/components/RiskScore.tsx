import { cn } from "@/lib/utils";

export function riskBand(score: number): "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" {
  if (score <= 30) return "LOW";
  if (score <= 60) return "MEDIUM";
  if (score <= 80) return "HIGH";
  return "CRITICAL";
}

const BAND_COLOR: Record<string, string> = {
  LOW: "text-safe",
  MEDIUM: "text-medium",
  HIGH: "text-high",
  CRITICAL: "text-critical",
};

const BAND_RING: Record<string, string> = {
  LOW: "stroke-safe",
  MEDIUM: "stroke-medium",
  HIGH: "stroke-high",
  CRITICAL: "stroke-critical",
};

/**
 * `invert`: pass true when `score` is a SECURITY/POSTURE score (higher = safer,
 * e.g. ScanRun.security_score_after) rather than a RISK score (higher = worse,
 * e.g. Vulnerability.risk_score). The color band is mirrored accordingly so a
 * high security score reads green, not red.
 */
export function RiskScoreGauge({ score, size = 76, label, invert = false }: { score: number; size?: number; label?: string; invert?: boolean }) {
  const band = riskBand(invert ? 100 - score : score);
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} strokeWidth={6} className="fill-none stroke-muted" />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={6}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={cn("fill-none transition-all duration-700", BAND_RING[band])}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("mono-tabular text-lg font-bold", BAND_COLOR[band])}>{score}</span>
        </div>
      </div>
      {label && <span className="text-[11px] text-muted-foreground">{label}</span>}
    </div>
  );
}

export function RiskBandLabel({ score, invert = false }: { score: number; invert?: boolean }) {
  const band = riskBand(invert ? 100 - score : score);
  return <span className={cn("text-xs font-semibold uppercase tracking-wide", BAND_COLOR[band])}>{band}</span>;
}
