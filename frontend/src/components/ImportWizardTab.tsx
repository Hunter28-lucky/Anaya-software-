"use client";

import React, { useState, useRef } from "react";
import { Project, UploadPreviewResponse, ColumnMapping } from "@/types";
import { uploadPreview, previewSheet, startBatch } from "@/lib/api";
import {
  UploadCloud,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle,
  Play,
  Database,
  Info,
  RefreshCw,
  Layers,
  ArrowRight,
  ShieldCheck,
  Check,
} from "lucide-react";

interface ImportWizardTabProps {
  selectedProject: Project | null;
  onBatchStarted: (batchId: string) => void;
}

export function ImportWizardTab({ selectedProject, onBatchStarted }: ImportWizardTabProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [previewData, setPreviewData] = useState<UploadPreviewResponse | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [startRow, setStartRow] = useState<number>(2);
  const [endRow, setEndRow] = useState<number>(2);
  const [mapping, setMapping] = useState<ColumnMapping>({ url_col: "" });
  const [updatingSheet, setUpdatingSheet] = useState(false);
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
      setSelectedSheet(data.selected_worksheet);
      setStartRow(data.start_row);
      setEndRow(data.end_row);
      setMapping(data.suggested_mapping);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process file preview.");
    } finally {
      setUploading(false);
    }
  };

  const handleWorksheetChange = async (sheetName: string) => {
    if (!previewData) return;
    setSelectedSheet(sheetName);
    setUpdatingSheet(true);
    setErrorMsg(null);

    try {
      const updated = await previewSheet({
        temp_file_id: previewData.temp_file_id,
        sheet_name: sheetName,
      });
      setPreviewData(updated);
      setSelectedSheet(updated.selected_worksheet);
      setStartRow(updated.start_row);
      setEndRow(updated.end_row);
      setMapping(updated.suggested_mapping);
    } catch (err: any) {
      setErrorMsg("Failed to switch worksheet: " + err.message);
    } finally {
      setUpdatingSheet(false);
    }
  };

  const handleApplyRowRange = async () => {
    if (!previewData) return;
    setUpdatingSheet(true);
    setErrorMsg(null);

    try {
      const updated = await previewSheet({
        temp_file_id: previewData.temp_file_id,
        sheet_name: selectedSheet,
        url_col: mapping.url_col,
        company_name_col: mapping.company_name_col,
        industry_col: mapping.industry_col,
        snov_result_col: mapping.snov_result_col,
        start_row: Number(startRow),
        end_row: Number(endRow),
      });
      setPreviewData(updated);
      setStartRow(updated.start_row);
      setEndRow(updated.end_row);
      setMapping(updated.suggested_mapping);
    } catch (err: any) {
      setErrorMsg("Failed to update range: " + err.message);
    } finally {
      setUpdatingSheet(false);
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
        sheet_name: selectedSheet,
        start_row: Number(startRow),
        end_row: Number(endRow),
        mapping: mapping,
      });
      onBatchStarted(batch.id);
    } catch (err: any) {
      alert("Error starting batch: " + err.message);
    } finally {
      setStartingBatch(false);
    }
  };

  const urlLetter = mapping.url_col ? previewData?.column_letters[mapping.url_col] || "B" : "B";
  const sourceSummaryText = previewData
    ? `Source: ${selectedSheet} | Column ${urlLetter} (${mapping.url_col || "url"}) | ${previewData.total_detected_rows.toLocaleString()} source rows`
    : "";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-cyan-400" />
          Excel Source Selection & Lead Import
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Select the exact worksheet and column mapping. Only records from the chosen worksheet are imported.
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
              {uploading ? "Inspecting Workbook Worksheets & Schema..." : "Drag & Drop Excel Workbook (.xlsx) or CSV"}
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              Supports multi-sheet workbooks. Defaults to <strong className="text-cyan-300">SNOV SEARCH</strong> worksheet when detected.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">
            Max file size: 50MB
          </span>
        </div>
      )}

      {/* Step 2: Excel Configuration & Live Preview */}
      {previewData && (
        <div className="space-y-6">
          {/* Top File Summary Bar */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-7 h-7 text-cyan-400" />
              <div>
                <span className="text-[11px] text-slate-400">Workbook File</span>
                <div className="text-sm font-bold text-white">{previewData.filename}</div>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <div className="px-3 py-1 rounded-lg bg-cyan-950/60 border border-cyan-800/40 text-cyan-300 font-medium">
                {sourceSummaryText}
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
          </div>

          {/* Worksheet & Row Configuration Card */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5 shadow-lg">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white">Excel Worksheet & Scope Configuration</h3>
              </div>
              <span className="text-xs text-emerald-400 flex items-center gap-1 font-semibold">
                <ShieldCheck className="w-3.5 h-3.5" />
                Strict Sheet Isolation Enabled
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* 1. Worksheet Selector */}
              <div>
                <label className="block text-xs font-semibold text-cyan-400 mb-1.5">
                  1. Source Worksheet *
                </label>
                <select
                  value={selectedSheet}
                  disabled={updatingSheet}
                  onChange={(e) => handleWorksheetChange(e.target.value)}
                  className="w-full bg-slate-950 border border-cyan-500/50 text-slate-100 text-xs rounded-xl px-3 py-2.5 font-medium focus:ring-2 focus:ring-cyan-500"
                >
                  {previewData.available_worksheets.map((s) => (
                    <option key={s} value={s}>
                      {s} {s.toLowerCase().includes("snov") ? "★ (Recommended Default)" : ""}
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Only rows from this worksheet will enter the pipeline.
                </p>
              </div>

              {/* 2. Start Row */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  2. Start Row (Header is Row 1)
                </label>
                <input
                  type="number"
                  min={2}
                  value={startRow}
                  disabled={updatingSheet}
                  onChange={(e) => setStartRow(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-cyan-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  First data row after headers (default: Row 2).
                </p>
              </div>

              {/* 3. End Row */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  3. End Row (Last Data Row)
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min={startRow}
                    value={endRow}
                    disabled={updatingSheet}
                    onChange={(e) => setEndRow(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-cyan-500"
                  />
                  <button
                    onClick={handleApplyRowRange}
                    disabled={updatingSheet}
                    title="Apply Range"
                    className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold shrink-0 transition-colors flex items-center gap-1"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${updatingSheet ? "animate-spin" : ""}`} />
                    Apply
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Auto-detected last valid row in this sheet.
                </p>
              </div>
            </div>

            {/* Column Mapping Selectors */}
            <div className="pt-2 border-t border-slate-800/80">
              <label className="block text-xs font-bold text-slate-200 mb-2 flex items-center gap-2">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                Column Mapping for Worksheet: <span className="text-cyan-300">{selectedSheet}</span>
              </label>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                {/* Website URL (Required) */}
                <div>
                  <label className="block text-xs font-semibold text-cyan-400 mb-1">
                    Website URL * (Required)
                  </label>
                  <select
                    value={mapping.url_col}
                    onChange={(e) => setMapping({ ...mapping, url_col: e.target.value })}
                    className="w-full bg-slate-950 border border-cyan-500/40 text-slate-100 text-xs rounded-xl px-3 py-2 focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="">-- Select Column --</option>
                    {previewData.detected_columns.map((c) => (
                      <option key={c} value={c}>
                        Column {previewData.column_letters[c] || "?"}: {c}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Company Name */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Company Name (Optional)
                  </label>
                  <select
                    value={mapping.company_name_col || ""}
                    onChange={(e) => setMapping({ ...mapping, company_name_col: e.target.value || undefined })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-xl px-3 py-2 focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="">-- None / Skip --</option>
                    {previewData.detected_columns.map((c) => (
                      <option key={c} value={c}>
                        Column {previewData.column_letters[c] || "?"}: {c}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Industry / Category */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Industry / Category (Optional)
                  </label>
                  <select
                    value={mapping.industry_col || ""}
                    onChange={(e) => setMapping({ ...mapping, industry_col: e.target.value || undefined })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-xl px-3 py-2 focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="">-- None / Skip --</option>
                    {previewData.detected_columns.map((c) => (
                      <option key={c} value={c}>
                        Column {previewData.column_letters[c] || "?"}: {c}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Snov Research Result */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Prior Snov Result (Optional)
                  </label>
                  <select
                    value={mapping.snov_result_col || ""}
                    onChange={(e) => setMapping({ ...mapping, snov_result_col: e.target.value || undefined })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-xl px-3 py-2 focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="">-- None / Skip --</option>
                    {previewData.detected_columns.map((c) => (
                      <option key={c} value={c}>
                        Column {previewData.column_letters[c] || "?"}: {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Stats & Warnings Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] text-slate-400">Total Rows in Scope</span>
              <div className="text-lg font-bold text-white mt-0.5">
                {previewData.total_detected_rows.toLocaleString()}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] text-slate-400">Valid Non-Empty URLs</span>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">
                {previewData.total_non_empty_urls.toLocaleString()}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] text-slate-400">Duplicate URLs</span>
              <div className={`text-lg font-bold mt-0.5 ${previewData.duplicate_url_count > 0 ? "text-amber-400" : "text-slate-400"}`}>
                {previewData.duplicate_url_count}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] text-slate-400">Malformed / Invalid URLs</span>
              <div className={`text-lg font-bold mt-0.5 ${previewData.invalid_url_count > 0 ? "text-rose-400" : "text-slate-400"}`}>
                {previewData.invalid_url_count}
              </div>
            </div>
          </div>

          {/* Warnings List */}
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

          {/* Parsed Record Preview (First 20 Records) */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>URL Preview — First {previewData.preview_records?.length || 10} Parsed Records</span>
                <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                  Worksheet: {selectedSheet}
                </span>
              </h3>
              <span className="text-xs text-slate-400">
                Active Header: <strong className="text-cyan-400">Column {urlLetter} ({mapping.url_col})</strong>
              </span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-96">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 sticky top-0 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Excel Row #</th>
                    <th className="py-2.5 px-3">Company Name</th>
                    <th className="py-2.5 px-3 text-cyan-400">Website URL</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {previewData.preview_records?.map((record) => (
                    <tr key={record.row_number} className="hover:bg-slate-850/50">
                      <td className="py-2 px-3 text-slate-500 font-mono">Row {record.row_number}</td>
                      <td className="py-2 px-3 font-medium text-slate-200 max-w-xs truncate">
                        {record.company_name || <span className="text-slate-600 italic">None</span>}
                      </td>
                      <td className="py-2 px-3 text-cyan-300 font-mono truncate max-w-md">
                        {record.url || <span className="text-rose-500/70 italic">Empty URL</span>}
                      </td>
                      <td className="py-2 px-3">
                        {record.is_valid_url ? (
                          record.is_duplicate ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950/60 text-amber-300 border border-amber-800/40">
                              Duplicate
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
                              Valid URL
                            </span>
                          )
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950/60 text-rose-300 border border-rose-800/40">
                            Malformed
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Bar with Confirm & Start Processing */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="text-xs text-slate-400 flex flex-col gap-0.5">
              <div className="flex items-center gap-1.5">
                <Info className="w-4 h-4 text-slate-500" />
                Target Project: <strong className="text-slate-200">{selectedProject?.name}</strong> (
                {selectedProject?.target_industry})
              </div>
              <div className="text-[11px] text-cyan-400 font-mono font-medium">
                {sourceSummaryText}
              </div>
            </div>

            <button
              onClick={handleStartBatch}
              disabled={startingBatch || !mapping.url_col || updatingSheet}
              className="flex items-center gap-2 px-7 py-3 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 cursor-pointer"
            >
              <Play className="w-4 h-4 fill-slate-950" />
              {startingBatch ? "Starting Processing Job..." : "Confirm & Start Processing"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
