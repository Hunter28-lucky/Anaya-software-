"use client";

import React, { useState } from "react";
import { ProjectRecord } from "@/types";
import { submitReviewOverride } from "@/lib/api";
import {
  X,
  ExternalLink,
  ShieldCheck,
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  FileText,
  Globe,
  Quote,
  Edit3,
  Check,
} from "lucide-react";

interface EvidenceDrawerProps {
  record: ProjectRecord | null;
  onClose: () => void;
  onRecordUpdated: (updated: ProjectRecord) => void;
}

export function EvidenceDrawer({ record, onClose, onRecordUpdated }: EvidenceDrawerProps) {
  if (!record) return null;

  const [newStatus, setNewStatus] = useState<string>(record.final_classification);
  const [overrideReason, setOverrideReason] = useState("");
  const [notes, setNotes] = useState("");
  const [reviewerName, setReviewerName] = useState("Lead Auditor");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overrideReason.trim()) {
      alert("Please provide an override reason.");
      return;
    }

    setSubmitting(true);
    try {
      const updated = await submitReviewOverride(record.id, {
        new_classification: newStatus,
        override_reason: overrideReason.trim(),
        notes: notes.trim() || undefined,
        reviewer_name: reviewerName.trim(),
      });
      setSuccess(true);
      onRecordUpdated(updated);
      setTimeout(() => setSuccess(false), 2500);
    } catch (err: any) {
      alert("Failed to submit review: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "MATCH":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">MATCH</span>;
      case "PARTIAL_MATCH":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/30">PARTIAL MATCH</span>;
      case "NOT_A_MATCH":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">NOT A MATCH</span>;
      case "NEEDS_REVIEW":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">NEEDS REVIEW</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-700 text-slate-300">UNVERIFIABLE</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm">
      <div className="w-full max-w-2xl h-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-950/60 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">
                Evidence Dossier
              </span>
              <span>•</span>
              {getStatusBadge(record.final_classification)}
              {record.is_reviewed && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  Human Reviewed
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              {record.company_name || record.domain || "Company Record"}
            </h2>
            <div className="flex items-center gap-3 mt-1.5 flex-wrap">
              <a
                href={record.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono"
              >
                <span>{record.website_url}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              {record.source_worksheet && (
                <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-cyan-300 border border-slate-700 font-mono">
                  Sheet: {record.source_worksheet} • Row #{record.row_index || "?"}
                </span>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-slate-300">
          {/* Executive Summary Card */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Core Business Summary
            </span>
            <p className="text-slate-200 text-sm leading-relaxed">
              {record.core_business_summary || "No automated business summary generated."}
            </p>
          </div>

          {/* Decision Rationale */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Qualification Decision Reason
            </span>
            <p className="text-slate-200 leading-relaxed">
              {record.decision_reason || "Decision reached via crawl evaluation."}
            </p>
            <div className="pt-2 border-t border-slate-850 flex flex-wrap gap-4 text-[11px] text-slate-400">
              <div>
                Relevance: <strong className="text-white">{record.business_relevance}</strong>
              </div>
              <div>
                Confidence: <strong className="text-white">{Math.round(record.confidence * 100)}%</strong>
              </div>
              <div>
                Evidence Quality: <strong className="text-white">{record.evidence_quality}</strong>
              </div>
            </div>
          </div>

          {/* Snov Comparison Card */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between gap-4">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Uploaded Snov Research Result
              </span>
              <div className="text-sm font-semibold text-white mt-0.5">
                {record.snov_result || "Not provided in import"}
              </div>
            </div>

            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Cross-Verification
              </span>
              <div className="mt-0.5">
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                    record.snov_verification === "SUPPORTED"
                      ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                      : record.snov_verification === "CONTRADICTED"
                      ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                      : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {record.snov_verification}
                </span>
              </div>
            </div>
          </div>

          {/* Crawl Coverage Stats */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Crawler Inspection Coverage
              </span>
              <span className="text-[11px] font-mono text-cyan-400">
                Status: {record.crawl_status || "N/A"}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center pt-1">
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-850">
                <div className="text-base font-bold text-white">{record.pages_discovered}</div>
                <div className="text-[10px] text-slate-400">Pages Discovered</div>
              </div>
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-850">
                <div className="text-base font-bold text-emerald-400">{record.pages_fetched}</div>
                <div className="text-[10px] text-slate-400">Pages Fetched</div>
              </div>
              <div className="p-2 rounded-lg bg-slate-900 border border-slate-850">
                <div className="text-base font-bold text-rose-400">{record.pages_failed}</div>
                <div className="text-[10px] text-slate-400">Pages Failed</div>
              </div>
            </div>
          </div>

          {/* Supporting Evidence Items */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle className="w-4 h-4" />
              Direct First-Party Supporting Evidence ({record.evidence_items.length})
            </h3>

            {record.evidence_items.length === 0 ? (
              <p className="text-slate-500 italic p-3 bg-slate-950/40 rounded-lg">
                No direct evidence excerpts extracted.
              </p>
            ) : (
              <div className="space-y-2.5">
                {record.evidence_items.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <a
                        href={ev.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] truncate flex items-center gap-1"
                      >
                        <Globe className="w-3 h-3 shrink-0" />
                        <span className="truncate">{ev.source_url}</span>
                      </a>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-400 shrink-0">
                        {ev.page_type || "PAGE"}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-850 text-slate-200 text-xs italic flex items-start gap-2">
                      <Quote className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
                      <span>{ev.excerpt}</span>
                    </div>

                    {ev.relevance && (
                      <p className="text-[11px] text-slate-400">
                        <strong className="text-slate-300">Auditor Note:</strong> {ev.relevance}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Limitations */}
          {record.limitations && record.limitations.length > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-900/30 text-amber-300 space-y-1">
              <span className="font-semibold block text-[11px]">Audit Coverage Limitations:</span>
              <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                {record.limitations.map((lim, i) => (
                  <li key={i}>{lim}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Manual Review & Override Form */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 to-cyan-950/20 border border-cyan-900/40 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Edit3 className="w-4 h-4 text-cyan-400" />
                Human Auditor Override
              </h3>
              {record.is_reviewed && (
                <span className="text-[11px] text-cyan-400 font-mono">
                  Previously reviewed by {record.reviewed_by}
                </span>
              )}
            </div>

            <form onSubmit={handleOverrideSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  New Classification Status
                </label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="MATCH">MATCH (Sufficient direct evidence)</option>
                  <option value="PARTIAL_MATCH">PARTIAL_MATCH (Secondary business / limited scope)</option>
                  <option value="NOT_A_MATCH">NOT_A_MATCH (Disqualified under criteria)</option>
                  <option value="NEEDS_REVIEW">NEEDS_REVIEW (Conflicting or ambiguous)</option>
                  <option value="UNVERIFIABLE">UNVERIFIABLE (Inaccessible or blocked)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Override Rationale *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Verified dedicated international patient desk on page /intl"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Additional Notes (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Internal notes for lead qualification team"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors shadow-lg shadow-cyan-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {success ? <Check className="w-4 h-4" /> : null}
                {submitting ? "Saving Override..." : success ? "Override Recorded" : "Submit Auditor Override"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
