"use client";

import React, { useState, useEffect } from "react";
import { ProjectRecord } from "@/types";
import { fetchRecords } from "@/lib/api";
import {
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  Eye,
  Download,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";

interface ResultsTabProps {
  projectId?: string;
  batchId?: string;
  onInspectEvidence: (record: ProjectRecord) => void;
  onOpenExport: () => void;
}

export function ResultsTab({
  projectId,
  batchId,
  onInspectEvidence,
  onOpenExport,
}: ResultsTabProps) {
  const [records, setRecords] = useState<ProjectRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [snovFilter, setSnovFilter] = useState("ALL");

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchRecords({
        project_id: projectId,
        batch_id: batchId,
        status: statusFilter,
        snov_verification: snovFilter,
        search: search.trim() || undefined,
        limit: 100,
      });
      setRecords(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId, batchId, statusFilter, snovFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "MATCH":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">MATCH</span>;
      case "PARTIAL_MATCH":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/30">PARTIAL</span>;
      case "NOT_A_MATCH":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">NOT A MATCH</span>;
      case "NEEDS_REVIEW":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">NEEDS REVIEW</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400">UNVERIFIABLE</span>;
    }
  };

  const getSnovBadge = (ver: string) => {
    switch (ver) {
      case "SUPPORTED":
        return <span className="text-emerald-400 font-semibold text-[11px] flex items-center gap-1"><CheckCircle className="w-3 h-3" /> SUPPORTED</span>;
      case "CONTRADICTED":
        return <span className="text-rose-400 font-semibold text-[11px] flex items-center gap-1"><XCircle className="w-3 h-3" /> CONTRADICTED</span>;
      default:
        return <span className="text-slate-400 text-[11px] flex items-center gap-1"><HelpCircle className="w-3 h-3" /> {ver}</span>;
    }
  };

  return (
    <div className="space-y-5">
      {/* Search & Actions Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <SlidersHorizontal className="w-5 h-5 text-cyan-400" />
            Qualification Results & Evidence Database
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Searchable lead classifications with direct website citations and Snov cross-checks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onOpenExport}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Download className="w-4 h-4" />
            <span>Download & Export</span>
          </button>

          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            title="Refresh Table"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search by company name, website domain, URL, or decision reason..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Search
          </button>
        </form>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-850 text-xs">
          <span className="text-slate-400 mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            Status:
          </span>
          {[
            { id: "ALL", label: "ALL" },
            { id: "MATCH", label: "CONFIRMED (MATCH)" },
            { id: "NOT_A_MATCH", label: "NOT A MATCH" },
            { id: "UNVERIFIABLE", label: "UNVERIFIABLE" },
            { id: "NEEDS_REVIEW", label: "NEEDS REVIEW" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setStatusFilter(item.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === item.id
                  ? "bg-cyan-500 text-slate-950 font-bold"
                  : "bg-slate-950 text-slate-400 hover:text-slate-200 hover:bg-slate-850 border border-slate-800"
              }`}
            >
              {item.label}
            </button>
          ))}

          <span className="text-slate-400 ml-4 mr-1">Snov Status:</span>
          {["ALL", "SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"].map((v) => (
            <button
              key={v}
              onClick={() => setSnovFilter(v)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                snovFilter === v
                  ? "bg-slate-200 text-slate-950 font-bold"
                  : "bg-slate-950 text-slate-400 hover:text-slate-200 hover:bg-slate-850 border border-slate-800"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Results Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Company & Domain</th>
              <th className="py-3 px-4">Website URL</th>
              <th className="py-3 px-4">Snov Result</th>
              <th className="py-3 px-4">Independent Status</th>
              <th className="py-3 px-4">Snov Check</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4">Crawl Coverage</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850">
            {records.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-500 italic">
                  {loading ? "Loading qualification records..." : "No records match the active filters."}
                </td>
              </tr>
            ) : (
              records.map((r) => (
                <tr key={r.id} className="hover:bg-slate-850/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">
                      {r.company_name || r.domain || "Unknown"}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5 flex items-center gap-1.5 flex-wrap">
                      <span>{r.domain}</span>
                      {r.source_worksheet && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-cyan-300 font-sans border border-slate-700">
                          {r.source_worksheet} • Row {r.row_index || "?"}
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="py-3 px-4">
                    <a
                      href={r.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono max-w-xs truncate"
                    >
                      <span className="truncate">{r.website_url}</span>
                      <ExternalLink className="w-3 h-3 shrink-0" />
                    </a>
                  </td>

                  <td className="py-3 px-4">
                    <span className="text-slate-300 font-medium">
                      {r.snov_result || <span className="text-slate-500">None</span>}
                    </span>
                  </td>

                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      {getStatusBadge(r.final_classification)}
                      {r.is_reviewed && (
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" title="Reviewed" />
                      )}
                    </div>
                  </td>

                  <td className="py-3 px-4">{getSnovBadge(r.snov_verification)}</td>

                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          style={{ width: `${Math.round(r.confidence * 100)}%` }}
                          className={`h-full ${
                            r.confidence >= 0.7
                              ? "bg-emerald-500"
                              : r.confidence >= 0.4
                              ? "bg-amber-500"
                              : "bg-rose-500"
                          }`}
                        />
                      </div>
                      <span className="font-mono text-[11px] text-slate-400">
                        {Math.round(r.confidence * 100)}%
                      </span>
                    </div>
                  </td>

                  <td className="py-3 px-4">
                    <div className="text-[11px] text-slate-300 font-medium">
                      {r.pages_fetched} pages fetched
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      {r.crawl_status || "UNKNOWN"}
                    </div>
                  </td>

                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onInspectEvidence(r)}
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-cyan-500 hover:text-slate-950 text-slate-200 border border-slate-700 hover:border-cyan-500 transition-all inline-flex items-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>Showing {records.length} records</span>
        <span>LeadQualify AI Deterministic Decision Engine</span>
      </div>
    </div>
  );
}
