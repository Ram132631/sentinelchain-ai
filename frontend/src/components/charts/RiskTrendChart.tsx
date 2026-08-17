import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function RiskTrendChart({ data }: { data: { date: string; score_before: number; score_after: number }[] }) {
  if (data.length === 0) {
    return <div className="flex h-[220px] items-center justify-center text-xs text-muted-foreground">Run a scan to build risk-trend history</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="scoreAfter" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="scoreBefore" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f87171" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#f87171" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={30} />
        <Tooltip contentStyle={{ background: "hsl(222 44% 8%)", border: "1px solid hsl(217 33% 18%)", borderRadius: 8, fontSize: 12 }} />
        <Area type="monotone" dataKey="score_before" name="Before" stroke="#f87171" fill="url(#scoreBefore)" strokeWidth={2} />
        <Area type="monotone" dataKey="score_after" name="After" stroke="#22d3ee" fill="url(#scoreAfter)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
