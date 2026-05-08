"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Server, Database, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { systemApi } from "@/lib/api";

const ServiceCard = ({ name, status, delay }: { name: string; status: string; delay: number }) => {
  const isHealthy = status === "healthy";
  const isUnavailable = status === "unavailable";

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}>
      <Card>
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isHealthy ? "bg-green-100 dark:bg-green-900/30" : "bg-red-100 dark:bg-red-900/30"}`}>
              <Server className={`w-4 h-4 ${isHealthy ? "text-green-600" : "text-red-600"}`} />
            </div>
            <div>
              <p className="font-medium text-sm capitalize">{name}</p>
              {status !== "healthy" && status !== "unavailable" && (
                <p className="text-xs text-muted-foreground truncate max-w-xs">{status}</p>
              )}
            </div>
          </div>
          <Badge variant={isHealthy ? "success" : isUnavailable ? "warning" : "destructive"}>
            {isHealthy ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
            {isHealthy ? "Healthy" : isUnavailable ? "Unavailable" : "Error"}
          </Badge>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default function SystemPage() {
  const [health, setHealth] = useState<any>(null);
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const [h, i] = await Promise.all([systemApi.health(), systemApi.info()]);
    setHealth(h);
    setInfo(i);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const services = health ? [
    { name: "PostgreSQL", status: health.postgres },
    { name: "Redis", status: health.redis },
    { name: "Qdrant Vector DB", status: health.qdrant },
    { name: "Ollama (Local AI)", status: health.ollama },
  ] : [];

  const allHealthy = services.every((s) => s.status === "healthy" || s.status === "unavailable");

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">System Health</h1>
          <p className="text-muted-foreground text-sm">Monitor infrastructure status</p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Refresh
        </Button>
      </div>

      {/* Overall status */}
      <Card className={allHealthy ? "border-green-200 bg-green-50/50 dark:bg-green-900/10" : "border-yellow-200 bg-yellow-50/50 dark:bg-yellow-900/10"}>
        <CardContent className="p-4 flex items-center gap-3">
          {allHealthy ? <CheckCircle className="w-5 h-5 text-green-600" /> : <AlertCircle className="w-5 h-5 text-yellow-600" />}
          <div>
            <p className="font-medium text-sm">{allHealthy ? "All systems operational" : "Some services degraded"}</p>
            <p className="text-xs text-muted-foreground">Last checked just now</p>
          </div>
        </CardContent>
      </Card>

      {/* Services */}
      <div className="space-y-2">
        {loading ? (
          [...Array(4)].map((_, i) => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)
        ) : (
          services.map((s, i) => <ServiceCard key={s.name} {...s} delay={i * 0.06} />)
        )}
      </div>

      {/* App Info */}
      {info && (
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-sm">Application Info</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(info).map(([k, v]) => (
                <div key={k}>
                  <p className="text-xs text-muted-foreground capitalize">{k.replace(/_/g, " ")}</p>
                  <p className="text-sm font-medium">{String(v)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Qdrant details */}
      {health?.qdrant_info && (
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-sm">Vector Store Stats</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Zap className="w-4 h-4 text-primary" />
              <div>
                <p className="text-sm font-medium">{health.qdrant_info.points_count?.toLocaleString()} vectors stored</p>
                <p className="text-xs text-muted-foreground">Status: {health.qdrant_info.status}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
