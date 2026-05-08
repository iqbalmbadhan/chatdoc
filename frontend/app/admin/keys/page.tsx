"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Key, Plus, Trash2, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { keysApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

const PROVIDERS = ["openai", "gemini", "deepseek", "openrouter", "qwen"];

export default function KeysPage() {
  const [keys, setKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ provider: "openai", key: "", label: "" });
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const data = await keysApi.list();
    setKeys(Array.isArray(data) ? data : []);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    if (!form.key.trim()) return;
    setSaving(true);
    await keysApi.create(form);
    setForm({ provider: "openai", key: "", label: "" });
    setSaving(false);
    load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this API key?")) return;
    await keysApi.delete(id);
    load();
  };

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">API Keys</h1>
        <p className="text-muted-foreground text-sm">Manage provider API keys (stored encrypted)</p>
      </div>

      {/* Add Key */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Add New Key</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Provider</Label>
              <select
                value={form.provider}
                onChange={(e) => setForm((f) => ({ ...f, provider: e.target.value }))}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
              >
                {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label>Label (optional)</Label>
              <Input
                placeholder="e.g. Production Key"
                value={form.label}
                onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>API Key</Label>
            <div className="relative">
              <Input
                type={showKey ? "text" : "password"}
                placeholder="sk-..."
                value={form.key}
                onChange={(e) => setForm((f) => ({ ...f, key: e.target.value }))}
                className="pr-10"
              />
              <button onClick={() => setShowKey(!showKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <Button onClick={handleSave} disabled={saving || !form.key.trim()} size="sm">
            <Plus className="w-4 h-4 mr-2" /> {saving ? "Saving..." : "Save Key"}
          </Button>
        </CardContent>
      </Card>

      {/* Existing Keys */}
      <div className="space-y-2">
        {loading ? (
          [...Array(3)].map((_, i) => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)
        ) : keys.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center">
              <Key className="w-7 h-7 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No API keys configured</p>
            </CardContent>
          </Card>
        ) : (
          keys.map((k, i) => (
            <motion.div key={k.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}>
              <Card>
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Key className="w-4 h-4 text-muted-foreground" />
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="capitalize text-xs">{k.provider}</Badge>
                        {k.label && <span className="text-sm font-medium">{k.label}</span>}
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5 font-mono">{k.key_hint || "****"}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground hidden sm:block">{formatRelativeTime(k.created_at)}</span>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={() => handleDelete(k.id)}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
