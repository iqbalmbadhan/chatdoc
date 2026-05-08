"use client";

import { useEffect, useState } from "react";
import { Search, MessageSquare, Trash2, Download, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { logsApi } from "@/lib/api";
import { formatRelativeTime, formatCost } from "@/lib/utils";

export default function ChatsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const load = async () => {
    setLoading(true);
    const data = await logsApi.chats({ page, page_size: 50, search: search || undefined });
    setLogs(data.items || []);
    setTotal(data.total || 0);
    setLoading(false);
  };

  useEffect(() => { load(); }, [page, search]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this log?")) return;
    await fetch(`/api/logs/chats/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Chat Logs</h1>
          <p className="text-muted-foreground text-sm">{total} total conversations</p>
        </div>
        <a href={logsApi.exportChats()} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="w-4 h-4" /> Export CSV
          </Button>
        </a>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search messages..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="pl-9"
        />
      </div>

      <div className="space-y-2">
        {loading ? (
          [...Array(5)].map((_, i) => <div key={i} className="h-20 rounded-lg bg-muted animate-pulse" />)
        ) : logs.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No chat logs yet</p>
            </CardContent>
          </Card>
        ) : (
          logs.map((log) => (
            <Card key={log.id} className="overflow-hidden">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {log.provider && <Badge variant="secondary" className="text-xs capitalize">{log.provider}</Badge>}
                      {log.model && <Badge variant="outline" className="text-xs">{log.model}</Badge>}
                      <span className="text-xs text-muted-foreground">{log.total_tokens} tokens</span>
                      <span className="text-xs text-muted-foreground">{formatCost(log.estimated_cost || 0)}</span>
                      <span className="text-xs text-muted-foreground">{log.latency_ms}ms</span>
                    </div>
                    <p className="text-sm line-clamp-2">{log.content}</p>

                    {expanded === log.id && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-medium text-muted-foreground">Full response:</p>
                        <p className="text-sm bg-muted/50 rounded-lg p-3 whitespace-pre-wrap text-xs">{log.content}</p>
                        {log.source_documents?.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">Sources used:</p>
                            <div className="space-y-1">
                              {log.source_documents.map((s: any, i: number) => (
                                <div key={i} className="text-xs bg-muted/30 rounded px-2 py-1">{s.filename} (score: {s.score})</div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-1 flex-shrink-0">
                    <span className="text-xs text-muted-foreground hidden sm:block">{formatRelativeTime(log.created_at)}</span>
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setExpanded(expanded === log.id ? null : log.id)}>
                      {expanded === log.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Page {page}</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Previous</Button>
          <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={logs.length < 50}>Next</Button>
        </div>
      </div>
    </div>
  );
}
