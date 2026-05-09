"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Trash2, RefreshCw, CheckCircle, XCircle, Clock, Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { docsApi } from "@/lib/api";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

const statusConfig: Record<string, { label: string; color: "success" | "warning" | "destructive" | "secondary" | "default"; icon: any }> = {
  indexed: { label: "Indexed", color: "success", icon: CheckCircle },
  processing: { label: "Processing", color: "warning", icon: Loader2 },
  pending: { label: "Pending", color: "secondary", icon: Clock },
  failed: { label: "Failed", color: "destructive", icon: XCircle },
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [search, setSearch] = useState("");

  const load = async () => {
    const [docsData, statsData] = await Promise.all([docsApi.list({ page_size: 100 }), docsApi.stats()]);
    setDocuments(docsData.items || []);
    setStats(statsData);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  // Poll every 3 s while any document is still processing or pending
  useEffect(() => {
    const hasPending = documents.some((d) => d.status === "pending" || d.status === "processing");
    if (!hasPending) return;
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, [documents]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);
    setUploadProgress(0);

    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      const formData = new FormData();
      formData.append("file", file);
      await docsApi.upload(formData);
      setUploadProgress(Math.round(((i + 1) / acceptedFiles.length) * 100));
    }

    setUploading(false);
    setUploadProgress(0);
    load();
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      // PDF
      "application/pdf": [".pdf"],
      // Microsoft Office — modern
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      // Microsoft Office — legacy
      "application/msword": [".doc"],
      "application/vnd.ms-excel": [".xls"],
      // OpenDocument (LibreOffice / macOS)
      "application/vnd.oasis.opendocument.text": [".odt"],
      "application/vnd.oasis.opendocument.spreadsheet": [".ods"],
      "application/vnd.oasis.opendocument.presentation": [".odp"],
      // Rich text & markup
      "application/rtf": [".rtf"],
      "text/rtf": [".rtf"],
      "text/html": [".html", ".htm"],
      "application/xml": [".xml"],
      "text/xml": [".xml"],
      "application/epub+zip": [".epub"],
      // Plain text variants
      "text/plain": [".txt", ".log", ".ini", ".cfg", ".conf", ".rst"],
      "text/markdown": [".md"],
      "application/toml": [".toml"],
      // Data / structured
      "text/csv": [".csv"],
      "text/tab-separated-values": [".tsv"],
      "application/json": [".json"],
      "application/x-yaml": [".yaml", ".yml"],
      "text/yaml": [".yaml", ".yml"],
    },
    multiple: true,
  });

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this document?")) return;
    try {
      await docsApi.delete(id);
    } finally {
      load();
    }
  };

  const handleReindex = async (id: string) => {
    await docsApi.reindex(id);
    load();
  };

  const filtered = documents.filter((d) =>
    d.original_filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Documents</h1>
          <p className="text-muted-foreground text-sm">Upload and manage your knowledge base</p>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total", value: stats.total_documents },
            { label: "Total Size", value: formatBytes(stats.total_size_bytes || 0) },
            { label: "Chunks", value: stats.total_chunks?.toLocaleString() },
            { label: "Tokens", value: stats.total_tokens?.toLocaleString() },
          ].map((s) => (
            <Card key={s.label} className="py-3">
              <CardContent className="p-0 px-4">
                <p className="text-xs text-muted-foreground">{s.label}</p>
                <p className="font-bold text-lg">{s.value || 0}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/50"
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-8 h-8 mx-auto mb-3 text-muted-foreground" />
        {uploading ? (
          <div className="space-y-2">
            <p className="text-sm font-medium">Uploading...</p>
            <Progress value={uploadProgress} className="max-w-xs mx-auto" />
          </div>
        ) : (
          <>
            <p className="font-medium text-sm">{isDragActive ? "Drop files here" : "Drop files or click to upload"}</p>
            <p className="text-xs text-muted-foreground mt-1">
              PDF · Word (DOC, DOCX) · Excel (XLS, XLSX) · PowerPoint (PPTX) · OpenDocument (ODT, ODS, ODP)
            </p>
            <p className="text-xs text-muted-foreground">
              RTF · HTML · XML · EPUB · CSV · TSV · JSON · YAML · TOML · TXT · MD · and more — max 50 MB
            </p>
          </>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search documents..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Document List */}
      <div className="space-y-2">
        {loading ? (
          [...Array(3)].map((_, i) => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)
        ) : filtered.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No documents yet. Upload your first document above.</p>
            </CardContent>
          </Card>
        ) : (
          <AnimatePresence>
            {filtered.map((doc, i) => {
              const status = statusConfig[doc.status] || statusConfig.pending;
              const StatusIcon = status.icon;
              return (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: i * 0.03 }}
                >
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <FileText className="w-4 h-4 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className="font-medium text-sm truncate">{doc.original_filename}</p>
                            <Badge variant={status.color as any} className="flex-shrink-0 text-xs">
                              <StatusIcon className={`w-3 h-3 mr-1 ${doc.status === "processing" ? "animate-spin" : ""}`} />
                              {status.label}
                            </Badge>
                          </div>
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-xs text-muted-foreground">
                            <span>{formatBytes(doc.file_size)}</span>
                            <span>{doc.page_count} pages</span>
                            <span>{doc.chunk_count} chunks</span>
                            <span>{formatRelativeTime(doc.created_at)}</span>
                          </div>
                          {doc.error_message && (
                            <p className="text-xs text-destructive mt-1 truncate">{doc.error_message}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-1 flex-shrink-0">
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleReindex(doc.id)} title="Re-index">
                            <RefreshCw className="w-3.5 h-3.5" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => handleDelete(doc.id)}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
