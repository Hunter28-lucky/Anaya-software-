"use client";

import React, { useState, useRef } from "react";
import { Project, UploadPreviewResponse, ColumnMapping } from "@/types";
import { uploadPreview, startBatch } from "@/lib/api";
import {
  UploadCloud,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle,
  Play,
  ArrowRight,
  Database,
  Info,
} from "lucide-react";

interface ImportWizardTabProps {
  selectedProject: Project | null;
  onBatchStarted: (batchId: string) => void;
}

export function ImportWizardTab({ selectedProject, onBatchStarted }: ImportWizardTabProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [previewData, setPreviewData] = useState<UploadPreviewResponse | null>(null);
  const [mapping, setMapping] = useState<ColumnMapping>({ url_col: "" });
  const [startingBatch, setStartingBatch] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const processSelectedFile = async (selectedFile: File) => {
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (!["csv", "xlsx", "xls"].includes(ext || "")) {
      setErrorMsg("Please upload a .csv or .xlsx Excel file.");
      return;
    }

    setFile(selectedFile);
    setErrorMsg(null);
    setUploading(true);

    try {
      const data = await uploadPreview(selectedFile);
      setPreviewData(data);
      setMapping(data.suggested_mapping);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process file preview.");
    } finally {
      setUploading(false);
    }
  };

  const handleStartBatch = async () => {
    if (!selectedProject || !previewData) return;
    if (!mapping.url_col) {
      alert("Please map the Website URL column before starting the batch.");
      return;
    }

    setStartingBatch(true);
    try {
      const batch = await startBatch({
        project_id: selectedProject.id,
        temp_file_id: previewData.temp_file_id,
        filename: previewData.filename,
        mapping: mapping,
      });
      onBatchStarted(batch.id);
    } catch (err: any) {
      alert("Error starting batch: " + err.message);
    } finally {
      setStartingBatch(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-cyan-400" />
          Lead Spreadsheet Import Wizard
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Upload Excel or CSV lead files, verify columns, inspect duplicate warnings, and launch background verification.
        </p>
      </div>

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Step 1: Upload Zone */}
      {!previewData && (
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-2xl p-12 text-center bg-slate-900/40 hover:bg-slate-900/70 cursor-pointer transition-all flex flex-col items-center justify-center gap-4"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                processSelectedFile(e.target.files[0]);
              }
            }}
          />
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/10">
            <FileSpreadsheet className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              {uploading ? "Analyzing File Schema..." : "Drag & Drop Lead Workbook or Browse"}
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              Supports .csv and .xlsx. Compatible with Snov.io exports, custom CRM sheets, and company URL lists.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">
            Max file size: 25MB
          </span>
        </div>
      )}

      {/* Step 2: Mapping & Preview Screen */}
      {previewData && (
        <div className="space-y-6">
          {/* File Summary Card */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-8 h-8 text-cyan-400" />
              <div>
                <span className="text-xs text-slate-400">Selected File</span>
                <div className="text-sm font-bold text-white">{previewData.filename}</div>
              </div>
            </div>

            <div className="flex items-center gap-6 text-xs">
              <div>
                <span className="text-slate-400">Total Rows:</span>{" "}
                <strong className="text-white">{previewData.total_detected_rows}</strong>
              </div>
              <div>
                <span className="text-slate-400">Detected Columns:</span>{" "}
                <strong className="text-white">{previewData.detected_columns.length}</strong>
              </div>
              {previewData.duplicate_url_count > 0 && (
                <div className="text-amber-400 font-semibold flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {previewData.duplicate_url_count} Duplicate URLs
                </div>
              )}
            </div>

            <button
              onClick={() => {
                setPreviewData(null);
                setFile(null);
              }}
              className="text-xs text-slate-400 hover:text-rose-400 transition-colors"
            >
              Choose different file
            </button>
          </div>

          {/* Warnings Bar */}
          {previewData.sample_warnings && previewData.sample_warnings.length > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-800/40 text-xs text-amber-300 space-y-1">
              {previewData.sample_warnings.map((w, i) => (
                <div key={i} className="flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}

          {/* Column Mapping Section */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-cyan-400" />
                Map Columns to Platform Fields
              </h3>
              <span className="text-xs text-slate-400">All original columns are preserved during export</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {/* URL Column (Required) */}
              <div>
                <label className="block text-xs font-semibold text-cyan-400 mb-1">
                  Website URL * (Required)
                </label>
                <select
                  value={mapping.url_col}
                  onChange={(e) => setMapping({ ...mapping, url_col: e.target.value })}
                  className="w-full bg-slate-950 border border-cyan-500/40 text-slate-100 text-xs rounded-lg px-2.5 py-2 focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="">-- Select Column --</option>
                  {previewData.detected_columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Company Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Company Name
                </label>
                <select
                  value={mapping.company_name_col || ""}
                  onChange={(e) => setMapping({ ...mapping, company_name_col: e.target.value || undefined })}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-lg px-2.5 py-2 focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="">-- Auto-infer or Skip --</option>
                  {previewData.detected_columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Snov Research Result */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Snov Research Result
                </label>
                <select
                  value={mapping.snov_result_col || ""}
                  onChange={(e) => setMapping({ ...mapping, snov_result_col: e.target.value || undefined })}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-lg px-2.5 py-2 focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="">-- None / Skip --</option>
                  {previewData.detected_columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Industry / Category */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Industry / Category
                </label>
                <select
                  value={mapping.industry_col || ""}
                  onChange={(e) => setMapping({ ...mapping, industry_col: e.target.value || undefined })}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-lg px-2.5 py-2 focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="">-- None / Skip --</option>
                  {previewData.detected_columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Row Preview Table */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white">Previewing First 10 Rows</h3>
            <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-72">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 sticky top-0 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">#</th>
                    {previewData.detected_columns.map((c) => (
                      <th
                        key={c}
                        className={`py-2.5 px-3 font-semibold ${
                          c === mapping.url_col ? "text-cyan-400 bg-cyan-950/20" : ""
                        }`}
                      >
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {previewData.preview_rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-850/50">
                      <td className="py-2 px-3 text-slate-500 font-mono">{idx + 1}</td>
                      {previewData.detected_columns.map((colName) => (
                        <td
                          key={colName}
                          className={`py-2 px-3 truncate max-w-xs ${
                            colName === mapping.url_col ? "text-cyan-300 font-mono" : ""
                          }`}
                        >
                          {String(row[colName] || "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-slate-500" />
              Target Project: <strong className="text-slate-200">{selectedProject?.name}</strong> (
              {selectedProject?.target_industry})
            </div>

            <button
              onClick={handleStartBatch}
              disabled={startingBatch || !mapping.url_col}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-slate-950" />
              {startingBatch ? "Starting Processing Job..." : "Confirm & Launch Background Verification"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
