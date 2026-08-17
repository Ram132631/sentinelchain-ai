import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Row { repository: string; critical: number; high: number; medium: number; low: number }

export function VulnsByRepoChart({ data }: { data: Row[] }) {
  if (data.length === 0) {
    return <div className="flex h-[220px] items-center justify-center text-xs text-muted-foreground">No repositories scanned yet</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" vertical={false} />
        <XAxis dataKey="repository" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={30} />
        <Tooltip
          cursor={{ fill: "hsla(189,94%,48%,0.06)" }}
          contentStyle={{ background: "hsl(222 44% 8%)", border: "1px solid hsl(217 33% 18%)", borderRadius: 8, fontSize: 12 }}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="critical" name="Critical" stackId="a" fill="#f87171" radius={[0, 0, 0, 0]} />
        <Bar dataKey="high" name="High" stackId="a" fill="#fb923c" />
        <Bar dataKey="medium" name="Medium" stackId="a" fill="#fbbf24" />
        <Bar dataKey="low" name="Low" stackId="a" fill="#38bdf8" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
