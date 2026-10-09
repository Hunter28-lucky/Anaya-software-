"use client";

import React, { useState, useEffect } from "react";
import { Project, ProjectStats, ImportBatch, ProjectRecord } from "@/types";
import {
  fetchProjects,
  fetchStats,
  fetchBatches,
  fetchHealth,
  createProject,
} from "@/lib/api";
import { Header } from "@/components/Header";
import { OverviewTab } from "@/components/OverviewTab";
import { ProjectsTab } from "@/components/ProjectsTab";
import { ImportWizardTab } from "@/components/ImportWizardTab";
import { BatchMonitorTab } from "@/components/BatchMonitorTab";
import { ResultsTab } from "@/components/ResultsTab";
import { EvidenceDrawer } from "@/components/EvidenceDrawer";
import { ExportDrawer } from "@/components/ExportDrawer";
import {
  BarChart3,
  Briefcase,
  UploadCloud,
  Activity,
  SlidersHorizontal,
  Plus,
} from "lucide-react";

export default function LeadQualifyDashboard() {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<ProjectRecord | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  // New Project Form state
  const [newProjectName, setNewProjectName] = useState("");
  const [newIndustry, setNewIndustry] = useState("Medical Tourism");
  const [newDesc, setNewDesc] = useState("");
  const [creatingProject, setCreatingProject] = useState(false);

  const checkHealth = async () => {
    try {
      const h = await fetchHealth();
      if (h.status === "healthy") setBackendOnline(true);
    } catch {
      setBackendOnline(false);
    }
  };

  const loadInitialData = async () => {
    try {
      const projList = await fetchProjects();
      setProjects(projList);
      if (projList.length > 0 && !selectedProject) {
        setSelectedProject(projList[0]);
      } else if (projList.length === 0) {
        // Create initial default project if empty
        const defaultProj = await createProject({
          name: "Medical Tourism Lead Qualification",
          target_industry: "Medical Tourism",
          description: "Cross-border healthcare facilitators and coordinators audit",
        });
        setProjects([defaultProj]);
        setSelectedProject(defaultProj);
      }
    } catch (err) {
      console.error("Error loading projects:", err);
    }
  };

  const loadProjectStatsAndBatches = async () => {
    if (!selectedProject) return;
    try {
      const s = await fetchStats(selectedProject.id);
      setStats(s);
      const b = await fetchBatches(selectedProject.id);
      setBatches(b);
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  useEffect(() => {
    checkHealth();
    loadInitialData();
    const healthInterval = setInterval(checkHealth, 10000);
    return () => clearInterval(healthInterval);
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadProjectStatsAndBatches();
      const statsInterval = setInterval(loadProjectStatsAndBatches, 4000);
      return () => clearInterval(statsInterval);
    }
  }, [selectedProject?.id]);

  const handleCreateNewProjectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    setCreatingProject(true);
    try {
      const created = await createProject({
        name: newProjectName.trim(),
        target_industry: newIndustry.trim(),
        description: newDesc.trim(),
      });
      setShowNewProjectModal(false);
      setNewProjectName("");
      setNewDesc("");
      const updatedList = await fetchProjects();
      setProjects(updatedList);
      setSelectedProject(created);
    } catch (err: any) {
      alert("Failed to create project: " + err.message);
    } finally {
      setCreatingProject(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Header */}
      <Header
        projects={projects}
        selectedProject={selectedProject}
        onSelectProject={(p) => setSelectedProject(p)}
        onOpenNewProject={() => setShowNewProjectModal(true)}
        backendOnline={backendOnline}
      />

      {/* Main Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Tab Navigation */}
        <div className="flex items-center gap-1.5 p-1.5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-md overflow-x-auto">
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === "overview"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-850"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Overview Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab("projects")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === "projects"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-850"
            }`}
          >
            <Briefcase className="w-4 h-4" />
            <span>Projects & Rules</span>
          </button>

          <button
            onClick={() => setActiveTab("import")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === "import"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-850"
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Import Wizard</span>
          </button>

          <button
            onClick={() => setActiveTab("batches")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === "batches"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-850"
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Batch Processing ({batches.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("results")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === "results"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-850"
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span>Qualification Results</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <OverviewTab
            stats={stats}
            activeBatches={batches}
            onNavigateToTab={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === "projects" && (
          <ProjectsTab
            projects={projects}
            selectedProject={selectedProject}
            onRefreshProjects={loadInitialData}
            onSelectProject={(p) => setSelectedProject(p)}
          />
        )}

        {activeTab === "import" && (
          <ImportWizardTab
            selectedProject={selectedProject}
            onBatchStarted={(batchId) => {
              setActiveTab("batches");
              loadProjectStatsAndBatches();
            }}
          />
        )}

        {activeTab === "batches" && (
          <BatchMonitorTab
            projectId={selectedProject?.id}
            onNavigateToResults={(batchId) => setActiveTab("results")}
          />
        )}

        {activeTab === "results" && (
          <ResultsTab
            projectId={selectedProject?.id}
            onInspectEvidence={(rec) => setSelectedRecord(rec)}
            onOpenExport={() => setShowExportModal(true)}
          />
        )}
      </div>

      {/* Slide-over Evidence Drawer */}
      <EvidenceDrawer
        record={selectedRecord}
        onClose={() => setSelectedRecord(null)}
        onRecordUpdated={(updated) => {
          setSelectedRecord(updated);
          loadProjectStatsAndBatches();
        }}
      />

      {/* Export Modal */}
      {showExportModal && selectedProject && (
        <ExportDrawer
          projectId={selectedProject.id}
          onClose={() => setShowExportModal(false)}
        />
      )}

      {/* New Project Modal */}
      {showNewProjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-3">Create New Qualification Project</h3>
            <form onSubmit={handleCreateNewProjectSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Project Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4 International Surgery Audit"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Target Industry
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Medical Tourism (or IT Outsourcing, SaaS)"
                  value={newIndustry}
                  onChange={(e) => setNewIndustry(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Purpose of this audit batch"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewProjectModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingProject}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors disabled:opacity-50"
                >
                  {creatingProject ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
