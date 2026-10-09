"use client";

import React from "react";
import { Project } from "@/types";
import { ShieldCheck, Plus, CheckCircle2, AlertCircle } from "lucide-react";

interface HeaderProps {
  projects: Project[];
  selectedProject: Project | null;
  onSelectProject: (p: Project) => void;
  onOpenNewProject: () => void;
  backendOnline: boolean;
}

export function Header({
  projects,
  selectedProject,
  onSelectProject,
  onOpenNewProject,
  backendOnline,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              LeadQualify AI
            </span>
            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              v1.0 Enterprise
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Evidence-Backed Website Qualification & Lead Filtering
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend status badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-slate-900 border border-slate-800">
          {backendOnline ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-300">FastAPI Active</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              <span className="text-amber-400">Connecting Backend</span>
            </>
          )}
        </div>

        {/* Project Switcher */}
        <div className="flex items-center gap-2">
          <label htmlFor="project-select" className="text-xs text-slate-400 hidden md:inline">
            Project:
          </label>
          <select
            id="project-select"
            value={selectedProject?.id || ""}
            onChange={(e) => {
              const p = projects.find((item) => item.id === e.target.value);
              if (p) onSelectProject(p);
            }}
            className="bg-slate-900 border border-slate-700 hover:border-slate-600 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-colors"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.target_industry})
              </option>
            ))}
          </select>

          <button
            onClick={onOpenNewProject}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-sm transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Project</span>
          </button>
        </div>
      </div>
    </header>
  );
}
