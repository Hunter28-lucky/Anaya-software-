"use client";

import React from "react";
import { ProjectStats, ImportBatch } from "@/types";
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Globe,
  Database,
  Search,
  Activity,
  Layers,
  Sparkles,
} from "lucide-react";

interface OverviewTabProps {
  stats: ProjectStats | null;
  activeBatches: ImportBatch[];
  onNavigateToTab: (tab: string) => void;
}

export function OverviewTab({ stats, activeBatches, onNavigateToTab }: OverviewTabProps) {
  const total = stats?.total_imported || 0;
  const matchPct = total > 0 ? Math.round(((stats?.match_count || 0) / total) * 100) : 0;
  const rejectedPct = total > 0 ? Math.round(((stats?.not_a_match_count || 0) / total) * 100) : 0;
  const reviewPct = total > 0 ? Math.round(((stats?.needs_review_count || 0) / total) * 100) : 0;
  const unverifiablePct = total > 0 ? Math.round(((stats?.unverifiable_count || 0) / total) * 100) : 0;
  const partialPct = total > 0 ? Math.round(((stats?.partial_match_count || 0) / total) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-cyan-950/40 border border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
              Evidence Engine Online
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Independent Business Qualification
          </h2>
          <p className="text-sm text-slate-300 max-w-2xl mt-1">
            Crawls first-party business pages, strips marketing noise, eliminates blog-only false positives,
            and validates Snov research with multi-page proof.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onNavigateToTab("import")}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            Import Excel / CSV
          </button>
          <button
            onClick={() => onNavigateToTab("results")}
            className="px-4 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            Inspect Evidence
          </button>
        </div>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Imported Records</span>
            <Database className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold text-white">{stats?.total_imported || 0}</div>
          <div className="text-[11px] text-slate-400 mt-1">Preserved source rows</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Unique Domains</span>
            <Globe className="w-4 h-4 text-cyan-500" />
          </div>
          <div className="text-2xl font-bold text-white">{stats?.unique_domains || 0}</div>
          <div className="text-[11px] text-cyan-400/90 mt-1">Deduplicated crawl targets</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Sites Crawled</span>
            <Search className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-white">{stats?.websites_crawled || 0}</div>
          <div className="text-[11px] text-blue-400/90 mt-1">SSRF-safe custom crawler</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Completed Classifications</span>
            <Layers className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-white">{stats?.completed_classifications || 0}</div>
          <div className="text-[11px] text-emerald-400/90 mt-1">Rule validated</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Avg Confidence</span>
            <Activity className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {stats?.average_confidence ? `${Math.round(stats.average_confidence * 100)}%` : "0%"}
          </div>
          <div className="text-[11px] text-violet-400/90 mt-1">Evidence confidence</div>
        </div>
      </div>

      {/* Classification Breakdown & Snov Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Classification Breakdown */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white">Qualification Decision Distribution</h3>
            <span className="text-xs text-slate-400">Total: {total} records</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-5">
            <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40">
              <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-semibold mb-1">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>MATCH</span>
              </div>
              <div className="text-xl font-bold text-emerald-300">{stats?.match_count || 0}</div>
              <div className="text-[11px] text-emerald-400/80 mt-0.5">{matchPct}% share</div>
            </div>

            <div className="p-3 rounded-xl bg-blue-950/30 border border-blue-800/40">
              <div className="flex items-center gap-1.5 text-blue-400 text-xs font-semibold mb-1">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>PARTIAL</span>
              </div>
              <div className="text-xl font-bold text-blue-300">{stats?.partial_match_count || 0}</div>
              <div className="text-[11px] text-blue-400/80 mt-0.5">{partialPct}% share</div>
            </div>

            <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-800/40">
              <div className="flex items-center gap-1.5 text-rose-400 text-xs font-semibold mb-1">
                <XCircle className="w-3.5 h-3.5" />
                <span>NOT A MATCH</span>
              </div>
              <div className="text-xl font-bold text-rose-300">{stats?.not_a_match_count || 0}</div>
              <div className="text-[11px] text-rose-400/80 mt-0.5">{rejectedPct}% share</div>
            </div>

            <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-800/40">
              <div className="flex items-center gap-1.5 text-amber-400 text-xs font-semibold mb-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>NEEDS REVIEW</span>
              </div>
              <div className="text-xl font-bold text-amber-300">{stats?.needs_review_count || 0}</div>
              <div className="text-[11px] text-amber-400/80 mt-0.5">{reviewPct}% share</div>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <div className="flex items-center gap-1.5 text-slate-400 text-xs font-semibold mb-1">
                <HelpCircle className="w-3.5 h-3.5" />
                <span>UNVERIFIABLE</span>
              </div>
              <div className="text-xl font-bold text-slate-300">{stats?.unverifiable_count || 0}</div>
              <div className="text-[11px] text-slate-400/80 mt-0.5">{unverifiablePct}% share</div>
            </div>
          </div>

          {/* Visual Progress Bar */}
          <div className="w-full h-3 rounded-full bg-slate-800 overflow-hidden flex">
            <div style={{ width: `${matchPct}%` }} className="bg-emerald-500 h-full" title={`MATCH ${matchPct}%`} />
            <div style={{ width: `${partialPct}%` }} className="bg-blue-500 h-full" title={`PARTIAL ${partialPct}%`} />
            <div style={{ width: `${rejectedPct}%` }} className="bg-rose-500 h-full" title={`NOT_A_MATCH ${rejectedPct}%`} />
            <div style={{ width: `${reviewPct}%` }} className="bg-amber-500 h-full" title={`NEEDS_REVIEW ${reviewPct}%`} />
            <div style={{ width: `${unverifiablePct}%` }} className="bg-slate-600 h-full" title={`UNVERIFIABLE ${unverifiablePct}%`} />
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
            <span>Deterministic qualification rules applied</span>
            <span>Zero hallucinated citations</span>
          </div>
        </div>

        {/* Snov Cross-Verification Breakdown */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-semibold text-white mb-1">Snov Research Verification</h3>
            <p className="text-xs text-slate-400 mb-4">
              Comparison between uploaded Snov status and independent website proof
            </p>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-900/30">
                <span className="text-xs text-emerald-300 font-medium">SUPPORTED (Confirmed)</span>
                <span className="text-sm font-bold text-emerald-400">{stats?.snov_supported_count || 0}</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-rose-950/20 border border-rose-900/30">
                <div>
                  <span className="text-xs text-rose-300 font-medium">CONTRADICTED (False Positives)</span>
                  <p className="text-[10px] text-rose-400/80">e.g. blog only or non-operational</p>
                </div>
                <span className="text-sm font-bold text-rose-400">{stats?.snov_contradicted_count || 0}</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40">
                <span className="text-xs text-slate-300 font-medium">INCONCLUSIVE (Missing / Inaccessible)</span>
                <span className="text-sm font-bold text-slate-400">{stats?.snov_inconclusive_count || 0}</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Agreement accuracy</span>
            <button
              onClick={() => onNavigateToTab("results")}
              className="text-cyan-400 hover:text-cyan-300 underline font-medium"
            >
              Filter contradictions
            </button>
          </div>
        </div>
      </div>

      {/* Active Batches */}
      {activeBatches && activeBatches.length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-white">Recent Processing Batches</h3>
            <button
              onClick={() => onNavigateToTab("batches")}
              className="text-xs text-cyan-400 hover:text-cyan-300"
            >
              View all batches
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activeBatches.slice(0, 2).map((b) => (
              <div key={b.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm text-slate-200">{b.filename}</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {b.processed_rows} of {b.total_rows} records processed
                  </div>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                    b.status === "COMPLETED"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : b.status === "PROCESSING"
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}
                >
                  {b.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
