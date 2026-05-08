"use client";

import { useEffect, useState } from "react";
import { MessageSquare, FileText, Users, DollarSign, Zap, Clock } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { StatCard } from "@/components/admin/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyticsApi } from "@/lib/api";
import { formatNumber, formatCost } from "@/lib/utils";

export default function AdminOverviewPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.overview(30).then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Overview</h1>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const stats = [
    { title: "Total Chats", value: formatNumber(data?.total_chats || 0), icon: MessageSquare, color: "violet" as const, delay: 0 },
    { title: "Documents", value: formatNumber(data?.total_documents || 0), icon: FileText, color: "blue" as const, delay: 0.05 },
    { title: "Visitors", value: formatNumber(data?.total_visitors || 0), icon: Users, color: "green" as const, delay: 0.1 },
    { title: "API Cost", value: formatCost(data?.total_cost || 0), icon: DollarSign, color: "orange" as const, delay: 0.15 },
    { title: "Total Tokens", value: formatNumber(data?.total_tokens || 0), icon: Zap, color: "blue" as const, delay: 0.2 },
    { title: "Avg Latency", value: `${Math.round(data?.avg_latency_ms || 0)}ms`, icon: Clock, color: "violet" as const, delay: 0.25 },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div>
        <h1 className="text-2xl font-bold">Overview</h1>
        <p className="text-muted-foreground text-sm mt-1">Last 30 days performance</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {stats.map((s) => (
          <StatCard key={s.title} {...s} />
        ))}
      </div>

      {/* Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Daily Chat Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.daily_stats || []}>
                  <defs>
                    <linearGradient id="chatGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ fontSize: 12 }} />
                  <Area type="monotone" dataKey="chat_count" stroke="hsl(var(--primary))" fill="url(#chatGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Provider Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(data?.provider_breakdown || {}).length === 0 ? (
                <p className="text-sm text-muted-foreground">No data yet</p>
              ) : (
                Object.entries(data?.provider_breakdown || {}).map(([provider, count]) => (
                  <div key={provider} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{provider}</span>
                    <span className="text-sm font-medium">{count as number}</span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
