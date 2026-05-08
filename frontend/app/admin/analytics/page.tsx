"use client";

import { useEffect, useState } from "react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/admin/StatCard";
import { Zap, DollarSign, MessageSquare, Clock } from "lucide-react";
import { analyticsApi } from "@/lib/api";
import { formatNumber, formatCost } from "@/lib/utils";

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.overview(30).then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6"><div className="h-48 bg-muted rounded-xl animate-pulse" /></div>;

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold">Usage Analytics</h1>
        <p className="text-muted-foreground text-sm">Token usage and cost tracking</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Chats" value={formatNumber(data?.total_chats || 0)} icon={MessageSquare} color="violet" delay={0} />
        <StatCard title="Total Tokens" value={formatNumber(data?.total_tokens || 0)} icon={Zap} color="blue" delay={0.05} />
        <StatCard title="API Cost" value={formatCost(data?.total_cost || 0)} icon={DollarSign} color="green" delay={0.1} />
        <StatCard title="Avg Latency" value={`${Math.round(data?.avg_latency_ms || 0)}ms`} icon={Clock} color="orange" delay={0.15} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Daily Chats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.daily_stats || []}>
                  <defs>
                    <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="chat_count" name="Chats" stroke="hsl(var(--primary))" fill="url(#g1)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Daily Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.daily_stats || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="token_count" name="Tokens" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Provider Usage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(data?.provider_breakdown || {}).map(([p, count]) => {
              const n = Number(count);
              const maxVal = Math.max(0, ...Object.values(data?.provider_breakdown || {}).map(Number));
              return (
                <div key={p} className="flex items-center gap-3">
                  <span className="text-sm w-24 capitalize">{p}</span>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${maxVal > 0 ? Math.min(100, (n / maxVal) * 100) : 0}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium w-10 text-right">{n}</span>
                </div>
              );
            })}
            {Object.keys(data?.provider_breakdown || {}).length === 0 && (
              <p className="text-sm text-muted-foreground">No data yet</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
