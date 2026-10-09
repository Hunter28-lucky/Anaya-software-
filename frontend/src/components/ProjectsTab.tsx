"use client";

import React, { useState } from "react";
import { Project, ProjectRule } from "@/types";
import { updateProjectRules, createProject } from "@/lib/api";
import { Settings, Plus, Check, Trash2, Sliders, Briefcase, Info } from "lucide-react";

interface ProjectsTabProps {
  projects: Project[];
  selectedProject: Project | null;
  onRefreshProjects: () => void;
  onSelectProject: (p: Project) => void;
}

export function ProjectsTab({
  projects,
  selectedProject,
  onRefreshProjects,
  onSelectProject,
}: ProjectsTabProps) {
  const [activeRule, setActiveRule] = useState<ProjectRule>(() => {
    return (
      selectedProject?.rules || {
        industry_definition:
          "Medical tourism facilitators, international patient coordinators, and cross-border healthcare travel agencies.",
        inclusion_criteria: [
          "Arranges cross-border medical treatments or healthcare travel",
          "Facilitates international patient intake, hospital coordination, and travel logistics",
          "Offers bundled medical packages with accredited overseas hospitals",
        ],
        exclusion_criteria: [
          "General travel agencies with no healthcare services",
          "Hospitals without dedicated international patient programs",
          "Websites that only mention medical tourism in blog articles or news",
        ],
        positive_examples: [
          { company: "Global Medical Care", reason: "Surgery packages and overseas hospital coordination" },
        ],
        negative_examples: [
          { company: "Wanderlust Holidays", reason: "General vacation booking agency with no medical partnerships" },
        ],
        confidence_threshold: 0.7,
      }
    );
  });

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [newInclusion, setNewInclusion] = useState("");
  const [newExclusion, setNewExclusion] = useState("");

  // New Project Form
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newIndustry, setNewIndustry] = useState("Medical Tourism");
  const [newDescription, setNewDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const handleSaveRules = async () => {
    if (!selectedProject) return;
    setSaving(true);
    try {
      await updateProjectRules(selectedProject.id, activeRule);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      onRefreshProjects();
    } catch (e) {
      alert("Error saving rules");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    setCreating(true);
    try {
      const created = await createProject({
        name: newProjectName.trim(),
        target_industry: newIndustry.trim(),
        description: newDescription.trim(),
      });
      setShowCreateModal(false);
      setNewProjectName("");
      setNewDescription("");
      onRefreshProjects();
      onSelectProject(created);
    } catch (err: any) {
      alert("Failed to create project: " + err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-cyan-400" />
            Project Configuration & Qualification Rules
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Configure target industry criteria, inclusion/exclusion rules, and confidence thresholds.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors shadow-lg shadow-cyan-500/20"
        >
          <Plus className="w-4 h-4" />
          Create New Project
        </button>
      </div>

      {/* Rules Config Card */}
      {selectedProject && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs uppercase tracking-wider text-cyan-400 font-semibold">
                Active Project
              </span>
              <h3 className="text-lg font-bold text-white">{selectedProject.name}</h3>
              <p className="text-xs text-slate-400">Target Industry: {selectedProject.target_industry}</p>
            </div>

            <button
              onClick={handleSaveRules}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-50"
            >
              {saveSuccess ? <Check className="w-4 h-4" /> : <Settings className="w-4 h-4" />}
              {saving ? "Saving..." : saveSuccess ? "Saved Successfully" : "Save Qualification Rules"}
            </button>
          </div>

          {/* Industry Definition */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Industry Definition & Core Mission
            </label>
            <textarea
              rows={3}
              value={activeRule.industry_definition}
              onChange={(e) =>
                setActiveRule({ ...activeRule, industry_definition: e.target.value })
              }
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 leading-relaxed"
            />
          </div>

          {/* Inclusion & Exclusion Columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Inclusion Criteria */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-emerald-400">
                  Inclusion Criteria (Must satisfy to qualify)
                </label>
                <span className="text-[11px] text-slate-400">
                  {activeRule.inclusion_criteria.length} rules
                </span>
              </div>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {activeRule.inclusion_criteria.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start justify-between gap-2 p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-900/30 text-xs text-emerald-200"
                  >
                    <span>{item}</span>
                    <button
                      onClick={() => {
                        const updated = activeRule.inclusion_criteria.filter((_, i) => i !== idx);
                        setActiveRule({ ...activeRule, inclusion_criteria: updated });
                      }}
                      className="text-slate-400 hover:text-rose-400 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Add Inclusion */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Coordinates international patient hospital admissions"
                  value={newInclusion}
                  onChange={(e) => setNewInclusion(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (newInclusion.trim()) {
                      setActiveRule({
                        ...activeRule,
                        inclusion_criteria: [...activeRule.inclusion_criteria, newInclusion.trim()],
                      });
                      setNewInclusion("");
                    }
                  }}
                  className="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg"
                >
                  Add
                </button>
              </div>
            </div>

            {/* Exclusion Criteria */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-rose-400">
                  Exclusion Criteria (Disqualifying characteristics)
                </label>
                <span className="text-[11px] text-slate-400">
                  {activeRule.exclusion_criteria.length} rules
                </span>
              </div>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {activeRule.exclusion_criteria.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start justify-between gap-2 p-2.5 rounded-lg bg-rose-950/20 border border-rose-900/30 text-xs text-rose-200"
                  >
                    <span>{item}</span>
                    <button
                      onClick={() => {
                        const updated = activeRule.exclusion_criteria.filter((_, i) => i !== idx);
                        setActiveRule({ ...activeRule, exclusion_criteria: updated });
                      }}
                      className="text-slate-400 hover:text-rose-400 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Add Exclusion */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Purely editorial blog with zero commercial coordination"
                  value={newExclusion}
                  onChange={(e) => setNewExclusion(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-rose-500"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (newExclusion.trim()) {
                      setActiveRule({
                        ...activeRule,
                        exclusion_criteria: [...activeRule.exclusion_criteria, newExclusion.trim()],
                      });
                      setNewExclusion("");
                    }
                  }}
                  className="px-3 py-1.5 text-xs bg-rose-600 hover:bg-rose-500 text-white rounded-lg"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Confidence Threshold Slider */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-semibold text-slate-200">
                  Minimum Confidence Threshold
                </span>
              </div>
              <span className="text-xs font-bold text-cyan-400">
                {Math.round(activeRule.confidence_threshold * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={activeRule.confidence_threshold}
              onChange={(e) =>
                setActiveRule({
                  ...activeRule,
                  confidence_threshold: parseFloat(e.target.value),
                })
              }
              className="w-full accent-cyan-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400 mt-2 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-slate-500" />
              Classifications with confidence below this threshold are automatically routed to
              NEEDS_REVIEW for human auditor inspection.
            </p>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-3">Create New Qualification Project</h3>
            <form onSubmit={handleCreateProject} className="space-y-4">
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
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-colors disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
