"use client";

import { useEffect, useState } from "react";
import { ScrollText, Info, AlertTriangle, XCircle, Bug } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { logsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

const levelConfig: Record<string, { color: string; icon: any }> = {
  debug: { color: "secondary", icon: Bug },
  info: { color: "default", icon: Info },
  warning: { color: "warning", icon: AlertTriangle },
  error: { color: "destructive", icon: XCircle },
  critical: { color: "destructive", icon: XCircle },
};

export default function LogsPage() {
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [activityLogs, setActivityLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([logsApi.system(), logsApi.activity()]).then(([s, a]) => {
      setSystemLogs(s.items || []);
      setActivityLogs(a.items || []);
    }).finally(() => setLoading(false));
  }, []);

  const LogEntry = ({ log }: { log: any }) => {
    const lc = levelConfig[log.level] || levelConfig.info;
    const Icon = lc.icon;
    return (
      <Card>
        <CardContent className="p-3">
          <div className="flex items-start gap-2">
            <Icon className="w-4 h-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <Badge variant={lc.color as any} className="text-xs capitalize">{log.level}</Badge>
                <span className="text-xs text-muted-foreground">{log.category}</span>
                <span className="text-xs text-muted-foreground ml-auto">{formatRelativeTime(log.created_at)}</span>
              </div>
              <p className="text-sm">{log.message}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const ActivityEntry = ({ log }: { log: any }) => (
    <Card>
      <CardContent className="p-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">{log.action}</p>
            <p className="text-xs text-muted-foreground">{log.ip_address} · {formatRelativeTime(log.created_at)}</p>
          </div>
          {log.target_type && <Badge variant="outline" className="text-xs">{log.target_type}</Badge>}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold">Logs</h1>
        <p className="text-muted-foreground text-sm">System and admin activity logs</p>
      </div>

      <Tabs defaultValue="system">
        <TabsList>
          <TabsTrigger value="system">System Logs</TabsTrigger>
          <TabsTrigger value="activity">Admin Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-2 mt-4">
          {loading ? (
            [...Array(5)].map((_, i) => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)
          ) : systemLogs.length === 0 ? (
            <Card><CardContent className="py-12 text-center"><p className="text-sm text-muted-foreground">No system logs</p></CardContent></Card>
          ) : (
            systemLogs.map((log) => <LogEntry key={log.id} log={log} />)
          )}
        </TabsContent>

        <TabsContent value="activity" className="space-y-2 mt-4">
          {loading ? (
            [...Array(5)].map((_, i) => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)
          ) : activityLogs.length === 0 ? (
            <Card><CardContent className="py-12 text-center"><p className="text-sm text-muted-foreground">No activity logs</p></CardContent></Card>
          ) : (
            activityLogs.map((log) => <ActivityEntry key={log.id} log={log} />)
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
