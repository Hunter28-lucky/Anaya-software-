"use client";

import React, { useState } from "react";
import { getExportDownloadUrl } from "@/lib/api";
import {
  X,
  Download,
  FileSpreadsheet,
  FileText,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
} from "lucide-react";

interface ExportDrawerProps {
  projectId: string;
  onClose: () => void;
}

export function ExportDrawer({ projectId, onClose }: ExportDrawerProps) {
  const [selectedFormat, setSelectedFormat] = useState<"xlsx" | "csv">("xlsx");

  const downloadLinks = [
    { label: "All Records (Complete Audit)", status: "ALL", icon: FileSpreadsheet, color: "text-cyan-400" },
    { label: "MATCH Records (Qualified Providers)", status: "MATCH", icon: CheckCircle, color: "text-emerald-400" },
    { label: "PARTIAL MATCH Records", status: "PARTIAL_MATCH", icon: CheckCircle, color: "text-blue-400" },
    { label: "NOT A MATCH Records (Disqualified)", status: "NOT_A_MATCH", icon: XCircle, color: "text-rose-400" },
    { label: "NEEDS REVIEW Records (Auditor Flagged)", status: "NEEDS_REVIEW", icon: AlertTriangle, color: "text-amber-400" },
    { label: "UNVERIFIABLE Records (Inaccessible)", status: "UNVERIFIABLE", icon: HelpCircle, color: "text-slate-400" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
              <Download className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Export & Download Records</h3>
              <p className="text-xs text-slate-400">
                Preserves all original import columns plus verification evidence
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Format Selection */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300">Choose File Format</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setSelectedFormat("xlsx")}
              className={`p-3 rounded-xl border text-left transition-all flex items-center gap-3 ${
                selectedFormat === "xlsx"
                  ? "border-cyan-500 bg-cyan-950/30 text-white"
                  : "border-slate-800 bg-slate-950 text-slate-400 hover:bg-slate-850"
              }`}
            >
              <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
              <div>
                <div className="text-xs font-bold">Excel (.xlsx)</div>
                <div className="text-[10px] text-slate-400">Multi-tab categorized workbook</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setSelectedFormat("csv")}
              className={`p-3 rounded-xl border text-left transition-all flex items-center gap-3 ${
                selectedFormat === "csv"
                  ? "border-cyan-500 bg-cyan-950/30 text-white"
                  : "border-slate-800 bg-slate-950 text-slate-400 hover:bg-slate-850"
              }`}
            >
              <FileText className="w-5 h-5 text-blue-400" />
              <div>
                <div className="text-xs font-bold">CSV (.csv)</div>
                <div className="text-[10px] text-slate-400">Flat tabular format</div>
              </div>
            </button>
          </div>
        </div>

        {/* Download Buttons List */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300">Select Export Subset</label>
          <div className="space-y-1.5">
            {downloadLinks.map((item) => {
              const url = getExportDownloadUrl(projectId, selectedFormat, item.status);
              const Icon = item.icon;
              return (
                <a
                  key={item.status}
                  href={url}
                  download
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 text-xs transition-colors group"
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${item.color}`} />
                    <span className="font-semibold text-slate-200 group-hover:text-white">
                      {item.label}
                    </span>
                  </div>
                  <Download className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                </a>
              );
            })}
          </div>
        </div>

        {/* Security Warning Notice */}
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <span>
            <strong>Formula Injection Safe (CWE-1236):</strong> All cell formulas starting with =, +, -, @,
            or pipe are securely sanitized with single quotes to protect your spreadsheet viewer from
            remote code execution.
          </span>
        </div>
      </div>
    </div>
  );
}
