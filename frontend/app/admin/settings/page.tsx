"use client";

import { useEffect, useState } from "react";
import { Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { settingsApi } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    settingsApi.get().then(setSettings).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    await settingsApi.update(settings);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (loading || !settings) return <div className="p-6"><div className="h-48 bg-muted rounded-xl animate-pulse" /></div>;

  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium">{label}</Label>
      {children}
    </div>
  );

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
          <Field label="Embedding Model">
            <Input value={settings.embedding_model} onChange={(e) => setSettings((s: any) => ({ ...s, embedding_model: e.target.value }))} />
          </Field>
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
            { key: "auto_delete_logs", label: "Auto-Delete Logs", desc: `Delete logs older than retention period` },
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
