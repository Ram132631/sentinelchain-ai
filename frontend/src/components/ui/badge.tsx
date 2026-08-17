import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default: "border-border bg-secondary text-secondary-foreground",
        outline: "border-border text-foreground bg-transparent",
        critical: "border-red-500/30 bg-red-500/15 text-red-400",
        high: "border-orange-500/30 bg-orange-500/15 text-orange-400",
        medium: "border-amber-500/30 bg-amber-500/15 text-amber-400",
        low: "border-sky-500/30 bg-sky-500/15 text-sky-400",
        safe: "border-emerald-500/30 bg-emerald-500/15 text-emerald-400",
        success: "border-emerald-500/30 bg-emerald-500/15 text-emerald-400",
        info: "border-cyan-500/30 bg-cyan-500/15 text-cyan-400",
        muted: "border-border bg-muted text-muted-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const variant = (severity?.toLowerCase() as BadgeProps["variant"]) || "muted";
  return <Badge variant={variant}>{severity}</Badge>;
}

export { Badge, badgeVariants };
