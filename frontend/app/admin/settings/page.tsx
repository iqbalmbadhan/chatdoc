"use client";

import { useEffect, useState } from "react";
import { Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { settingsApi } from "@/lib/api";

type EmbeddingModel = { id: string; dim: number };
type EmbeddingProviderOption = {
  display_name: string;
  requires_api_key: boolean;
  models: EmbeddingModel[];
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [embeddingProviders, setEmbeddingProviders] = useState<Record<string, EmbeddingProviderOption>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    Promise.all([settingsApi.get(), settingsApi.embeddingProviders()])
      .then(([s, ep]) => { setSettings(s); setEmbeddingProviders(ep); })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    await settingsApi.update(settings);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleEmbeddingProviderChange = (provider: string) => {
    const firstModel = embeddingProviders[provider]?.models[0]?.id ?? "";
    setSettings((s: any) => ({ ...s, embedding_provider: provider, embedding_model: firstModel }));
  };

  if (loading || !settings) return <div className="p-6"><div className="h-48 bg-muted rounded-xl animate-pulse" /></div>;

  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium">{label}</Label>
      {children}
    </div>
  );

  const currentProviderModels = embeddingProviders[settings.embedding_provider]?.models ?? [];

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground text-sm">Configure platform behaviour</p>
        </div>
        <Button onClick={handleSave} disabled={saving} size="sm">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {saved ? "Saved!" : "Save Settings"}
        </Button>
      </div>

      {/* RAG */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm">RAG Configuration</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          <Field label="Chunk Size (words)">
            <Input type="number" value={settings.chunk_size} onChange={(e) => setSettings((s: any) => ({ ...s, chunk_size: parseInt(e.target.value) }))} />
          </Field>
          <Field label="Chunk Overlap (words)">
            <Input type="number" value={settings.chunk_overlap} onChange={(e) => setSettings((s: any) => ({ ...s, chunk_overlap: parseInt(e.target.value) }))} />
          </Field>
          <Field label="Top-K Results">
            <Input type="number" value={settings.top_k} onChange={(e) => setSettings((s: any) => ({ ...s, top_k: parseInt(e.target.value) }))} />
          </Field>
          <div /> {/* grid spacer */}
          <Field label="Embedding Provider">
            <Select value={settings.embedding_provider} onValueChange={handleEmbeddingProviderChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(embeddingProviders).map(([key, p]) => (
                  <SelectItem key={key} value={key}>{p.display_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="Embedding Model">
            <Select
              value={settings.embedding_model}
              onValueChange={(v) => setSettings((s: any) => ({ ...s, embedding_model: v }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                {currentProviderModels.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    {m.id} <span className="text-muted-foreground ml-1">({m.dim}d)</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          {embeddingProviders[settings.embedding_provider]?.requires_api_key && (
            <p className="col-span-2 text-xs text-amber-600">
              This provider requires an API key — configure it in the Models &amp; Providers page.
            </p>
          )}
        </CardContent>
      </Card>

      {/* AI */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm">AI Defaults</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          <Field label="Default Provider">
            <Input value={settings.default_provider} onChange={(e) => setSettings((s: any) => ({ ...s, default_provider: e.target.value }))} />
          </Field>
          <Field label="Default Model">
            <Input value={settings.default_model} onChange={(e) => setSettings((s: any) => ({ ...s, default_model: e.target.value }))} />
          </Field>
          <div className="col-span-2">
            <Field label="System Prompt (optional)">
              <Textarea
                rows={4}
                placeholder="You are a helpful AI assistant..."
                value={settings.system_prompt || ""}
                onChange={(e) => setSettings((s: any) => ({ ...s, system_prompt: e.target.value }))}
              />
            </Field>
          </div>
        </CardContent>
      </Card>

      {/* Privacy */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm">Privacy & Compliance</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "ip_anonymization", label: "IP Anonymization", desc: "Store anonymized IPs only" },
            { key: "gdpr_consent", label: "GDPR Consent Mode", desc: "Show consent banner to visitors" },
            { key: "auto_delete_logs", label: "Auto-Delete Logs", desc: "Delete logs older than retention period" },
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">{label}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </div>
              <Switch
                checked={settings[key]}
                onCheckedChange={(v) => setSettings((s: any) => ({ ...s, [key]: v }))}
              />
            </div>
          ))}
          <Field label="Log Retention (days)">
            <Input
              type="number"
              className="max-w-xs"
              value={settings.log_retention_days}
              onChange={(e) => setSettings((s: any) => ({ ...s, log_retention_days: parseInt(e.target.value) }))}
            />
          </Field>
        </CardContent>
      </Card>

      {/* Limits */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-sm">Limits</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          <Field label="Max Upload Size (MB)">
            <Input type="number" value={settings.max_upload_size_mb} onChange={(e) => setSettings((s: any) => ({ ...s, max_upload_size_mb: parseInt(e.target.value) }))} />
          </Field>
          <Field label="Rate Limit (requests/min)">
            <Input type="number" value={settings.rate_limit_per_minute} onChange={(e) => setSettings((s: any) => ({ ...s, rate_limit_per_minute: parseInt(e.target.value) }))} />
          </Field>
        </CardContent>
      </Card>
    </div>
  );
}
