import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS: Record<string, string> = {
  CRITICAL: "#f87171",
  HIGH: "#fb923c",
  MEDIUM: "#fbbf24",
  LOW: "#38bdf8",
};

export function SeverityDistributionChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));

  if (chartData.length === 0) {
    return <div className="flex h-[200px] items-center justify-center text-xs text-muted-foreground">No vulnerabilities recorded yet</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={52} outerRadius={78} paddingAngle={3} strokeWidth={0}>
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name] || "#94a3b8"} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: "hsl(222 44% 8%)", border: "1px solid hsl(217 33% 18%)", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#e2e8f0" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
