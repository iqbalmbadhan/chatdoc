"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Cpu, CheckCircle, XCircle, Settings2, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { providersApi } from "@/lib/api";

export default function ModelsPage() {
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState<string | null>(null);

  const load = async () => {
    const data = await providersApi.list();
    setProviders(Array.isArray(data) ? data : []);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleToggle = async (provider: any, field: string, value: boolean) => {
    await providersApi.update(provider.id, { [field]: value });
    load();
  };

  const handleSetDefault = async (provider: any) => {
    await providersApi.update(provider.id, { is_default: true, is_enabled: true });
    load();
  };

  const handleValidate = async (name: string) => {
    setValidating(name);
    try {
      const result = await providersApi.validate(name);
      alert(result.valid ? `✅ ${name} connection is valid!` : `❌ ${name} connection failed`);
    } finally {
      setValidating(null);
    }
  };

  const providerIcons: Record<string, string> = {
    openai: "🤖",
    gemini: "✨",
    deepseek: "🔮",
    openrouter: "🌐",
    ollama: "🦙",
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold">AI Models</h1>
        <p className="text-muted-foreground text-sm">Configure AI providers and models</p>
      </div>

      <div className="grid gap-4">
        {loading
          ? [...Array(5)].map((_, i) => <div key={i} className="h-28 rounded-xl bg-muted animate-pulse" />)
          : providers.map((p, i) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
              <Card className={p.is_default ? "border-primary/40 shadow-md" : ""}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{providerIcons[p.name] || "🔌"}</div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-sm">{p.display_name}</h3>
                          {p.is_default && <Badge variant="default" className="text-xs">Default</Badge>}
                          {p.is_enabled && !p.is_default && <Badge variant="success" className="text-xs">Enabled</Badge>}
                        </div>
                        {p.default_model && <p className="text-xs text-muted-foreground mt-0.5">Model: {p.default_model}</p>}
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2">
                      <div className="flex items-center gap-2">
                        <Label htmlFor={`enable-${p.id}`} className="text-xs">Enabled</Label>
                        <Switch
                          id={`enable-${p.id}`}
                          checked={p.is_enabled}
                          onCheckedChange={(v) => handleToggle(p, "is_enabled", v)}
                        />
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-7"
                        onClick={() => handleSetDefault(p)}
                        disabled={p.is_default}
                      >
                        <Star className="w-3 h-3 mr-1" />
                        {p.is_default ? "Default" : "Set Default"}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs h-7"
                        onClick={() => handleValidate(p.name)}
                        disabled={validating === p.name}
                      >
                        {validating === p.name ? "Testing..." : "Test"}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
      </div>
    </div>
  );
}
