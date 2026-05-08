"use client";

import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/admin/StatCard";
import { Users, Globe, Monitor, Smartphone } from "lucide-react";
import { analyticsApi, visitorsApi } from "@/lib/api";

const COLORS = ["hsl(var(--chart-1))", "hsl(var(--chart-2))", "hsl(var(--chart-3))", "hsl(var(--chart-4))", "hsl(var(--chart-5))"];

export default function VisitorsPage() {
  const [stats, setStats] = useState<any>(null);
  const [visitors, setVisitors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsApi.visitors(30), visitorsApi.list()]).then(([s, v]) => {
      setStats(s);
      setVisitors(v.items || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6"><div className="h-48 bg-muted rounded-xl animate-pulse" /></div>;

  const deviceData = Object.entries(stats?.device_breakdown || {}).map(([name, value]) => ({ name, value }));
  const browserData = Object.entries(stats?.browser_breakdown || {}).slice(0, 5).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold">Visitor Analytics</h1>
        <p className="text-muted-foreground text-sm">Track who visits your platform</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Visitors" value={stats?.total_visitors || 0} icon={Users} color="blue" delay={0} />
        <StatCard title="Countries" value={stats?.unique_countries || 0} icon={Globe} color="green" delay={0.05} />
        <StatCard title="Desktop %" value={`${stats?.desktop_pct || 0}%`} icon={Monitor} color="violet" delay={0.1} />
        <StatCard title="Mobile %" value={`${stats?.mobile_pct || 0}%`} icon={Smartphone} color="orange" delay={0.15} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Device Types</CardTitle></CardHeader>
          <CardContent>
            {deviceData.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">No data yet</p>
            ) : (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={deviceData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false} fontSize={11}>
                      {deviceData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Top Browsers</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {browserData.length === 0 ? (
                <p className="text-sm text-muted-foreground">No data yet</p>
              ) : (
                browserData.map(({ name, value }, i) => (
                  <div key={name} className="flex items-center gap-3">
                    <span className="text-sm w-24 truncate">{name}</span>
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${Math.min(100, ((value as number) / browserData[0].value as number) * 100)}%`, backgroundColor: COLORS[i] }} />
                    </div>
                    <span className="text-sm font-medium">{value as number}</span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Countries */}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">Top Countries</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(stats?.country_breakdown || {}).slice(0, 12).map(([country, count]) => (
              <div key={country} className="flex items-center justify-between px-3 py-2 rounded-lg bg-muted/50">
                <span className="text-sm">{country}</span>
                <span className="text-sm font-semibold">{count as number}</span>
              </div>
            ))}
            {Object.keys(stats?.country_breakdown || {}).length === 0 && (
              <p className="text-sm text-muted-foreground col-span-3">No data yet</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
