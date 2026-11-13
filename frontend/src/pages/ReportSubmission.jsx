import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { StatusBadge, PriorityBadge, CategoryBadge } from '../components/StatusBadge';
import { 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Send, 
  ShieldAlert, 
  Cpu, 
  Clock, 
  MapPin, 
  Info,
  RefreshCw
} from 'lucide-react';

export const ReportSubmission = ({ onSubmitted }) => {
  const [formData, setFormData] = useState({
    reporter_name: 'Officer Johnathan Reed',
    reporter_contact: '+1-555-0188',
    report_code: '',
    signal_id: 'SIG-ZONA-101',
    zone: 'ZONE-A',
    location: 'Main St & 4th Ave Intersection',
    description: '',
    category: '',
    priority: 'MEDIUM'
  });

  const [dfaValidation, setDfaValidation] = useState(null);
  const [classificationPreview, setClassificationPreview] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [zones, setZones] = useState([]);

  // Fetch zones on load
  useEffect(() => {
    api.getZones().then(res => setZones(res.zones || [])).catch(() => {});
    handleGenerateId();
  }, []);

  // Generate ID handler
  const handleGenerateId = async () => {
    try {
      const res = await api.generateReportId();
      if (res && res.generated_id) {
        setFormData(prev => ({ ...prev, report_code: res.generated_id }));
        validateIdLive(res.generated_id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Live DFA & Regex Validation
  const validateIdLive = async (val) => {
    if (!val) {
      setDfaValidation(null);
      return;
    }
    try {
      const res = await api.simulateDFA(val);
      setDfaValidation(res);
    } catch (err) {
      console.error(err);
    }
  };

  // Live Classification Preview
  const handleDescriptionChange = async (e) => {
    const text = e.target.value;
    setFormData(prev => ({ ...prev, description: text }));

    if (text.length >= 4) {
      try {
        const preview = await api.previewClassification(text);
        setClassificationPreview(preview);
        // Automatically adopt suggested priority if user hasn't explicitly changed it
        if (preview.suggested_priority) {
          setFormData(prev => ({ 
            ...prev, 
            category: preview.primary_category,
            priority: preview.suggested_priority 
          }));
        }
      } catch (err) {
        console.error(err);
      }
    } else {
      setClassificationPreview(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    setSubmissionResult(null);

    try {
      const res = await api.submitReport(formData);
      setSubmissionResult(res);
      if (onSubmitted) onSubmitted(res);
    } catch (err) {
      console.error(err);
      if (err.data && err.data.validation_errors) {
        const errList = Object.values(err.data.validation_errors).join(' | ');
        setErrorMessage(errList);
      } else if (err.data && err.data.error) {
        setErrorMessage(err.data.error);
      } else {
        setErrorMessage('Failed to submit report. Please check server connection.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 uppercase tracking-wider mb-1 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Intelligent Ingestion Module</span>
            </div>
            <h2 className="text-2xl font-black text-slate-100 tracking-tight">
              Traffic Signal Fault Report Ingestion
            </h2>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Submit real-time traffic signal fault telemetry. Verified via formal Deterministic Finite Automaton (DFA) state validation and 5-category NLP classification prior to automated routing.
            </p>
          </div>
          <div className="flex items-center space-x-3 bg-slate-950/80 border border-slate-800 px-4 py-2.5 rounded-xl font-mono text-xs text-slate-300">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span>UTC {new Date().toISOString().slice(0, 19).replace('T', ' ')}</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Form Left, Real-Time Validation Telemetry Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: 7 cols */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Report Code with DFA Live Indicator */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                  Report Identifier (DFA Verified) *
                </label>
                <button
                  type="button"
                  onClick={handleGenerateId}
                  className="text-xs font-mono text-emerald-400 hover:text-emerald-300 flex items-center space-x-1 transition"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Auto Generate</span>
                </button>
              </div>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={formData.report_code}
                  onChange={(e) => {
                    setFormData({ ...formData, report_code: e.target.value });
                    validateIdLive(e.target.value);
                  }}
                  placeholder="TSF-2026-00001"
                  className={`w-full bg-slate-950 border px-4 py-3 rounded-xl font-mono text-sm tracking-wider text-slate-100 placeholder-slate-600 focus:outline-none transition ${
                    dfaValidation
                      ? dfaValidation.is_accepted
                        ? 'border-emerald-500/80 focus:border-emerald-400'
                        : 'border-red-500/80 focus:border-red-400'
                      : 'border-slate-800 focus:border-cyan-500'
                  }`}
                />
                <div className="absolute right-3 top-3 flex items-center space-x-1.5">
                  {dfaValidation && (
                    dfaValidation.is_accepted ? (
                      <span className="flex items-center text-xs font-mono text-emerald-400 bg-emerald-950/80 border border-emerald-500/50 px-2 py-0.5 rounded">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> DFA VALID
                      </span>
                    ) : (
                      <span className="flex items-center text-xs font-mono text-red-400 bg-red-950/80 border border-red-500/50 px-2 py-0.5 rounded">
                        <AlertCircle className="w-3 h-3 mr-1" /> MALFORMED
                      </span>
                    )
                  )}
                </div>
              </div>
              {dfaValidation && !dfaValidation.is_accepted && (
                <p className="text-xs text-red-400 font-mono mt-1.5">
                  ⚠️ {dfaValidation.error_reason}
                </p>
              )}
            </div>

            {/* Reporter Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                  Reporter Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.reporter_name}
                  onChange={(e) => setFormData({ ...formData, reporter_name: e.target.value })}
                  placeholder="Officer or Citizen name"
                  className="w-full bg-slate-950 border border-slate-800 px-3.5 py-2.5 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-emerald-500 transition"
                />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                  Reporter Contact *
                </label>
                <input
                  type="text"
                  required
                  value={formData.reporter_contact}
                  onChange={(e) => setFormData({ ...formData, reporter_contact: e.target.value })}
                  placeholder="+1-555-0100"
                  className="w-full bg-slate-950 border border-slate-800 px-3.5 py-2.5 rounded-xl text-sm font-mono text-slate-100 focus:outline-none focus:border-emerald-500 transition"
                />
              </div>
            </div>

            {/* Signal & Zone Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                  Traffic Signal ID *
                </label>
                <input
                  type="text"
                  required
                  value={formData.signal_id}
                  onChange={(e) => setFormData({ ...formData, signal_id: e.target.value })}
                  placeholder="SIG-ZONA-101"
                  className="w-full bg-slate-950 border border-slate-800 px-3.5 py-2.5 rounded-xl text-sm font-mono text-slate-100 focus:outline-none focus:border-emerald-500 transition"
                />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                  Zone Identifier *
                </label>
                <select
                  value={formData.zone}
                  onChange={(e) => setFormData({ ...formData, zone: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 px-3.5 py-2.5 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-emerald-500 transition"
                >
                  {zones.map((z) => (
                    <option key={z.id} value={z.zone_code}>
                      {z.zone_code} - {z.name}
                    </option>
                  ))}
                  <option value="ZONE-UNKNOWN-99">Unknown Zone (Test Fallback Queue)</option>
                </select>
              </div>
            </div>

            {/* Intersection Location */}
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-amber-400" />
                Intersection / Street Location *
              </label>
              <input
                type="text"
                required
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g. Broad St & 7th Ave Junction"
                className="w-full bg-slate-950 border border-slate-800 px-3.5 py-2.5 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>

            {/* Fault Description with Live Classifier Preview */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  Fault Description (Auto-Classified) *
                </label>
                <span className="text-[11px] font-mono text-slate-500">Live Keyword NLP</span>
              </div>
              <textarea
                required
                rows={3}
                value={formData.description}
                onChange={handleDescriptionChange}
                placeholder="Describe the issue (e.g., 'Red light not working and green bulb is burnt out' or 'Unexpected signal switching and timer duration incorrect')"
                className="w-full bg-slate-950 border border-slate-800 p-3.5 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition"
              ></textarea>
            </div>

            {/* Detected Category & Priority Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                  Category (Auto-Detected)
                </label>
                <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-xl flex items-center justify-between">
                  {formData.category ? (
                    <CategoryBadge category={formData.category} />
                  ) : (
                    <span className="text-xs text-slate-500 italic">Type description above...</span>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                  Priority Level *
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 px-3.5 py-2.5 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-emerald-500 transition font-mono"
                >
                  <option value="LOW">LOW - Routine Maintenance</option>
                  <option value="MEDIUM">MEDIUM - Standard Traffic Flow</option>
                  <option value="HIGH">HIGH - Major Intersections / Delays</option>
                  <option value="CRITICAL">CRITICAL - Severe Hazard</option>
                  <option value="EMERGENCY">EMERGENCY - All Lights Off / Collision Risk</option>
                </select>
              </div>
            </div>

            {/* Error Message Alert */}
            {errorMessage && (
              <div className="bg-red-950/80 border border-red-500/50 p-4 rounded-xl text-xs text-red-300 font-mono flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">SUBMISSION REJECTED:</span> {errorMessage}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || (dfaValidation && !dfaValidation.is_accepted)}
              className={`w-full py-3.5 px-6 rounded-xl font-bold text-sm tracking-wide transition-all shadow-lg flex items-center justify-center space-x-2 ${
                isSubmitting || (dfaValidation && !dfaValidation.is_accepted)
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20 hover:shadow-emerald-500/30'
              }`}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Validating & Dispatching...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit Report & Execute Dispatch Algorithm</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Telemetry Column: 5 cols */}
        <div className="lg:col-span-5 space-y-6">
          {/* Live DFA State Telemetry Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-mono uppercase text-cyan-400 font-semibold flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                DFA State Transition Trace
              </h3>
              <span className="text-[10px] font-mono bg-cyan-950 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800">
                14-State Automaton
              </span>
            </div>

            {dfaValidation ? (
              <div className="mt-4 space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div>
                    <span className="text-slate-500 block text-[10px]">CURRENT STATE</span>
                    <span className={`font-bold text-sm ${dfaValidation.is_accepted ? 'text-emerald-400' : 'text-red-400'}`}>
                      {dfaValidation.final_state}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">REGEX EQUIVALENCE</span>
                    <span className="text-slate-200">
                      {dfaValidation.equivalent ? '✓ 100% Equivalent' : '✗ Discrepancy'}
                    </span>
                  </div>
                </div>

                {/* Transition steps carousel preview */}
                <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                  {dfaValidation.steps?.map((st) => (
                    <div
                      key={st.step}
                      className="bg-slate-950/70 p-2 rounded-lg border border-slate-800/80 flex items-center justify-between text-[11px]"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-slate-500">#{st.step}</span>
                        <span className="bg-slate-800 text-cyan-300 px-1.5 py-0.2 rounded font-bold">
                          '{st.char}'
                        </span>
                        <span className="text-slate-400">{st.from_state} →</span>
                        <span className="text-emerald-400 font-bold">{st.to_state}</span>
                      </div>
                      <span className="text-[10px] text-slate-500 truncate max-w-[140px] text-right">
                        {st.explanation}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs font-mono">
                Enter or generate a report ID to inspect DFA state transitions.
              </div>
            )}
          </div>

          {/* Live Classification Scoring Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-mono uppercase text-emerald-400 font-semibold flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Classification Telemetry
              </h3>
              <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800">
                Exact 5 Categories
              </span>
            </div>

            {classificationPreview ? (
              <div className="mt-4 space-y-3 font-mono text-xs">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Primary Category Resolution</div>
                  <div className="text-sm font-bold text-slate-100 mt-1 flex items-center justify-between">
                    <span>{classificationPreview.primary_category}</span>
                    <span className="text-xs text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded">
                      {Math.round(classificationPreview.confidence_score * 100)}% Conf
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">
                    {classificationPreview.resolution_rule}
                  </div>
                </div>

                {/* Candidate categories list */}
                <div className="space-y-1.5">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Candidate Scores</div>
                  {classificationPreview.candidates?.map((c) => (
                    <div
                      key={c.category}
                      className="bg-slate-950/60 p-2 rounded-lg border border-slate-800 flex items-center justify-between text-[11px]"
                    >
                      <span className="truncate max-w-[200px] text-slate-300">{c.category}</span>
                      <span className="text-emerald-400 font-bold bg-slate-800 px-2 py-0.5 rounded">
                        Score: {c.score}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs font-mono">
                Start typing description to view NLP classification scores.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Submission Result Modal / Banner */}
      {submissionResult && (
        <div className="bg-emerald-950/90 border border-emerald-500 p-6 rounded-2xl shadow-2xl text-slate-100 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-emerald-500/30">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              <div>
                <h3 className="text-lg font-bold text-emerald-300">
                  Report {submissionResult.report.report_code} Dispatched Successfully
                </h3>
                <p className="text-xs text-slate-300 font-mono">
                  Saved in SQLite database and processed through dispatch sequence.
                </p>
              </div>
            </div>
            <StatusBadge status={submissionResult.report.status} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div className="bg-slate-950/80 p-3 rounded-xl border border-emerald-900/50">
              <span className="text-slate-400 block text-[10px]">DISPATCH DECISION</span>
              <strong className="text-emerald-300 text-sm">
                {submissionResult.dispatch_decision.decision}
              </strong>
            </div>
            <div className="bg-slate-950/80 p-3 rounded-xl border border-emerald-900/50">
              <span className="text-slate-400 block text-[10px]">ASSIGNED HANDLER</span>
              <strong className="text-slate-100 text-sm">
                {submissionResult.dispatch_decision.assigned_handler?.name || 'Central / Escalation Queue'}
              </strong>
            </div>
            <div className="bg-slate-950/80 p-3 rounded-xl border border-emerald-900/50">
              <span className="text-slate-400 block text-[10px]">CONFIRMED PRIORITY</span>
              <PriorityBadge priority={submissionResult.report.priority} />
            </div>
          </div>

          <div className="text-xs text-slate-300 bg-slate-950/90 p-3 rounded-xl border border-slate-800">
            <strong>Routing Reason:</strong> {submissionResult.dispatch_decision.reason}
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => {
                setSubmissionResult(null);
                handleGenerateId();
              }}
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs transition"
            >
              Submit Another Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
