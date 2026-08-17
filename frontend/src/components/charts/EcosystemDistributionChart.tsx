import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function EcosystemDistributionChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));
  if (chartData.length === 0) {
    return <div className="flex h-[200px] items-center justify-center text-xs text-muted-foreground">No SBOM components yet</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={30} />
        <Tooltip
          cursor={{ fill: "hsla(189,94%,48%,0.06)" }}
          contentStyle={{ background: "hsl(222 44% 8%)", border: "1px solid hsl(217 33% 18%)", borderRadius: 8, fontSize: 12 }}
        />
        <Bar dataKey="value" fill="#22d3ee" radius={[4, 4, 0, 0]} maxBarSize={40} />
      </BarChart>
    </ResponsiveContainer>
  );
}
