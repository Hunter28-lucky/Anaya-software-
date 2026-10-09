"use client";

import React, { useEffect, useState } from "react";
import { ImportBatch } from "@/types";
import { fetchBatches, pauseBatch, resumeBatch, cancelBatch } from "@/lib/api";
import {
  Activity,
  Pause,
  Play,
  XCircle,
  RefreshCw,
  Clock,
  CheckCircle,
  AlertTriangle,
  FileText,
} from "lucide-react";

interface BatchMonitorTabProps {
  projectId?: string;
  onNavigateToResults: (batchId: string) => void;
}

export function BatchMonitorTab({ projectId, onNavigateToResults }: BatchMonitorTabProps) {
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [loading, setLoading] = useState(false);

  const loadBatches = async () => {
    try {
      const data = await fetchBatches(projectId);
      setBatches(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadBatches();
    const interval = setInterval(loadBatches, 3000); // Polling every 3 seconds for live updates
    return () => clearInterval(interval);
  }, [projectId]);

  const handlePause = async (id: string) => {
    await pauseBatch(id);
    loadBatches();
  };

  const handleResume = async (id: string) => {
    await resumeBatch(id);
    loadBatches();
  };

  const handleCancel = async (id: string) => {
    if (confirm("Are you sure you want to cancel this processing batch?")) {
      await cancelBatch(id);
      loadBatches();
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            Background Processing & Crawler Batches
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time status of crawling and AI verification pipelines. Auto-refreshes every 3 seconds.
          </p>
        </div>

        <button
          onClick={() => {
            setLoading(true);
            loadBatches().finally(() => setLoading(false));
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {batches.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 text-slate-400">
          <Clock className="w-10 h-10 mx-auto text-slate-600 mb-2" />
          <p className="text-sm">No processing batches found for this project yet.</p>
          <p className="text-xs text-slate-500 mt-1">
            Import an Excel or CSV file in the Import Wizard to start processing.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {batches.map((b) => {
            const pct = b.total_rows > 0 ? Math.round((b.processed_rows / b.total_rows) * 100) : 0;
            return (
              <div
                key={b.id}
                className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-750 transition-all space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-cyan-400">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">{b.filename}</h3>
                      {b.source_summary && (
                        <div className="text-xs text-cyan-300 font-semibold font-mono mt-0.5">
                          {b.source_summary}
                        </div>
                      )}
                      <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                        <span>Created {new Date(b.created_at).toLocaleString()}</span>
                        <span>•</span>
                        <span>Batch ID: {b.id.slice(0, 8)}...</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        b.status === "COMPLETED"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : b.status === "PROCESSING"
                          ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse"
                          : b.status === "PAUSED"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {b.status}
                    </span>

                    {b.status === "PROCESSING" && (
                      <button
                        onClick={() => handlePause(b.id)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                        title="Pause Batch"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}

                    {b.status === "PAUSED" && (
                      <button
                        onClick={() => handleResume(b.id)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 transition-colors"
                        title="Resume Batch"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}

                    {["PROCESSING", "QUEUED", "PAUSED"].includes(b.status) && (
                      <button
                        onClick={() => handleCancel(b.id)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950 text-rose-400 transition-colors"
                        title="Cancel Batch"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}

                    <button
                      onClick={() => onNavigateToResults(b.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                    >
                      View Records
                    </button>
                  </div>
                </div>

                {/* Progress Bar & Counters */}
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                    <span>
                      Progress: <strong className="text-white">{b.processed_rows}</strong> of{" "}
                      <strong className="text-white">{b.total_rows}</strong> rows ({pct}%)
                    </span>
                    <span>
                      MATCH: {b.matched_rows} | PARTIAL: {b.partial_rows} | NOT A MATCH: {b.rejected_rows} |
                      REVIEW: {b.review_rows}
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      style={{ width: `${pct}%` }}
                      className={`h-full transition-all duration-500 ${
                        b.status === "COMPLETED" ? "bg-emerald-500" : "bg-cyan-500"
                      }`}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
