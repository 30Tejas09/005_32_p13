import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { StatusBadge, PriorityBadge, CategoryBadge } from '../components/StatusBadge';
import { 
  Wrench, 
  Power, 
  Sliders, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Play, 
  MapPin, 
  RefreshCw,
  Check,
  FileCheck2,
  X
} from 'lucide-react';

export const HandlerDashboard = ({ currentUser }) => {
  const [handlers, setHandlers] = useState([]);
  const [selectedHandlerId, setSelectedHandlerId] = useState(null);
  const [handlerData, setHandlerData] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolvingAssignment, setResolvingAssignment] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchHandlers = async () => {
    try {
      const res = await api.getHandlers();
      setHandlers(res.handlers || []);
      if (!selectedHandlerId && res.handlers?.length > 0) {
        // If current user is handler, select matching handler or default to first
        const match = res.handlers.find(h => h.name.toLowerCase().includes(currentUser.username.toLowerCase()) || h.handler_code === 'HND-001');
        setSelectedHandlerId(match ? match.id : res.handlers[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchHandlerDetails = async (id) => {
    if (!id) return;
    setLoading(true);
    try {
      const hData = await api.getHandler(id);
      setHandlerData(hData);
      const asgData = await api.getHandlerAssignments(id);
      setAssignments(asgData.assignments || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHandlers();
  }, []);

  useEffect(() => {
    if (selectedHandlerId) {
      fetchHandlerDetails(selectedHandlerId);
    }
  }, [selectedHandlerId]);

  const toggleAvailability = async () => {
    if (!handlerData) return;
    try {
      const res = await api.updateHandlerAvailability(handlerData.id, !handlerData.is_available);
      setHandlerData(prev => ({ ...prev, is_available: res.handler.is_available }));
      fetchHandlers();
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateCapacity = async (newCap) => {
    if (!handlerData || newCap < 1) return;
    try {
      const res = await api.updateHandlerCapacity(handlerData.id, newCap);
      setHandlerData(prev => ({ ...prev, max_capacity: res.handler.max_capacity, remaining_capacity: res.handler.remaining_capacity }));
      fetchHandlers();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStartWork = async (assignmentId) => {
    setIsUpdating(true);
    try {
      await api.updateAssignmentStatus(assignmentId, 'IN_PROGRESS', 'Technician dispatched and work commenced onsite.', handlerData.name);
      fetchHandlerDetails(handlerData.id);
    } catch (err) {
      console.error(err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleMarkResolved = async () => {
    if (!resolvingAssignment) return;
    setIsUpdating(true);
    try {
      await api.updateAssignmentStatus(
        resolvingAssignment.id,
        'RESOLVED',
        resolutionNotes || 'Technician resolved signal issue and verified operational telemetry.',
        handlerData.name
      );
      setResolvingAssignment(null);
      setResolutionNotes('');
      fetchHandlerDetails(handlerData.id);
      fetchHandlers();
    } catch (err) {
      console.error(err);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header & Handler Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
            <Wrench className="w-6 h-6 text-emerald-400" />
            Field Maintenance & Handler Operations
          </h2>
          <p className="text-sm text-slate-400">
            Manage handler availability, dispatch assignments, and resolve traffic signal faults.
          </p>
        </div>

        {/* Handler Selector Dropdown */}
        <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 p-2 rounded-2xl">
          <span className="text-xs font-mono text-slate-400 uppercase pl-2">Active Handler:</span>
          <select
            value={selectedHandlerId || ''}
            onChange={(e) => setSelectedHandlerId(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 px-3 py-1.5 rounded-xl text-xs font-mono text-emerald-400 font-bold focus:outline-none"
          >
            {handlers.map((h) => (
              <option key={h.id} value={h.id}>
                {h.handler_code} - {h.name} ({h.zone_code})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Handler Status & Capacity Card */}
      {handlerData && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div className="flex items-center space-x-4">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-lg ${
                handlerData.is_available ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-red-500/20 text-red-400 border border-red-500/40'
              }`}>
                {handlerData.handler_code.slice(-3)}
              </div>
              <div>
                <h3 className="text-lg font-black text-slate-100 flex items-center gap-2">
                  {handlerData.name}
                  <span className="text-xs font-mono text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                    {handlerData.zone_code}
                  </span>
                </h3>
                <p className="text-xs text-slate-400 font-mono">
                  {handlerData.email} • {handlerData.phone}
                </p>
              </div>
            </div>

            {/* Availability Toggle and Capacity Stepper */}
            <div className="flex flex-wrap items-center gap-4">
              <button
                onClick={toggleAvailability}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-mono font-bold transition shadow-lg ${
                  handlerData.is_available
                    ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/40'
                }`}
              >
                <Power className="w-4 h-4" />
                <span>{handlerData.is_available ? 'ONLINE / AVAILABLE' : 'OFFLINE / UNAVAILABLE'}</span>
              </button>

              <div className="flex items-center space-x-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 text-xs font-mono">
                <span className="text-slate-400">MAX CAP:</span>
                <input
                  type="number"
                  min="1"
                  max="15"
                  value={handlerData.max_capacity}
                  onChange={(e) => handleUpdateCapacity(Number(e.target.value))}
                  className="w-12 bg-slate-900 border border-slate-700 text-center font-bold text-slate-100 rounded py-0.5"
                />
              </div>
            </div>
          </div>

          {/* Workload Progress Bar & Capabilities */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">CURRENT WORKLOAD UTILIZATION</span>
                <span className="font-bold text-slate-200">
                  {handlerData.current_workload} / {handlerData.max_capacity} tasks ({handlerData.remaining_capacity} remaining slots)
                </span>
              </div>
              <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div
                  className={`h-full transition-all duration-500 ${
                    handlerData.current_workload >= handlerData.max_capacity
                      ? 'bg-red-500'
                      : handlerData.current_workload / handlerData.max_capacity > 0.6
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                  }`}
                  style={{ width: `${Math.min(100, (handlerData.current_workload / handlerData.max_capacity) * 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Supported Categories</span>
              <div className="flex flex-wrap gap-1">
                {handlerData.supported_categories?.map((cat) => (
                  <span key={cat} className="text-[10px] font-mono bg-slate-950 text-slate-300 border border-slate-800 px-2 py-0.5 rounded">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Assigned Tasks List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>Active & Assigned Incidents</span>
            <span className="text-xs font-mono bg-emerald-950 text-emerald-400 px-2.5 py-0.5 rounded-full border border-emerald-800 font-bold">
              {assignments.filter(a => a.status === 'ACTIVE').length} Active
            </span>
          </h3>
          <button
            onClick={() => fetchHandlerDetails(selectedHandlerId)}
            className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center space-x-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-mono">Loading assigned reports...</div>
        ) : assignments.length === 0 ? (
          <div className="py-12 text-center text-slate-500 font-mono">
            No reports currently assigned to this technician.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {assignments.map((asg) => {
              const rep = asg.report_details;
              if (!rep) return null;
              const isActive = asg.status === 'ACTIVE';

              return (
                <div
                  key={asg.id}
                  className={`border rounded-2xl p-5 space-y-4 transition-all ${
                    isActive
                      ? 'bg-slate-950/80 border-slate-800 hover:border-emerald-500/50 shadow-lg'
                      : 'bg-slate-950/40 border-slate-800/40 opacity-70'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-sm text-cyan-400">{rep.report_code}</span>
                        <PriorityBadge priority={rep.priority} />
                      </div>
                      <div className="text-xs text-slate-400 font-sans mt-1 flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span>{rep.location}</span>
                      </div>
                    </div>
                    <StatusBadge status={rep.status} />
                  </div>

                  <p className="text-xs text-slate-300 font-sans bg-slate-900/90 p-3 rounded-xl border border-slate-800/60 leading-relaxed">
                    {rep.description}
                  </p>

                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                    <CategoryBadge category={rep.category} />
                    <span>Assigned: {asg.assigned_at?.slice(0, 16).replace('T', ' ')}</span>
                  </div>

                  {/* Action Buttons */}
                  {isActive && (
                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-end space-x-2">
                      {rep.status !== 'IN_PROGRESS' && (
                        <button
                          disabled={isUpdating}
                          onClick={() => handleStartWork(asg.id)}
                          className="bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs px-3.5 py-1.5 rounded-xl transition flex items-center space-x-1.5"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>Start Work</span>
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setResolvingAssignment(asg);
                          setResolutionNotes('');
                        }}
                        className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold font-mono text-xs px-3.5 py-1.5 rounded-xl transition flex items-center space-x-1.5 shadow-sm"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Mark Resolved</span>
                      </button>
                    </div>
                  )}

                  {!isActive && asg.resolution_notes && (
                    <div className="bg-emerald-950/30 border border-emerald-900/40 p-2.5 rounded-xl text-xs text-emerald-300 font-sans">
                      <strong>Resolution Note:</strong> {asg.resolution_notes}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Resolution Modal */}
      {resolvingAssignment && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <FileCheck2 className="w-5 h-5 text-emerald-400" />
                Resolve Incident {resolvingAssignment.report_code}
              </h3>
              <button onClick={() => setResolvingAssignment(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5 font-semibold">
                Technical Resolution Notes *
              </label>
              <textarea
                rows={4}
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="Detail the repairs performed (e.g. replaced burnt red aspect LED module, recalibrated detector loop sensitivity, reset power breaker)..."
                className="w-full bg-slate-950 border border-slate-800 p-3 rounded-xl text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
              ></textarea>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => setResolvingAssignment(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs px-4 py-2 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                disabled={isUpdating}
                onClick={handleMarkResolved}
                className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold font-mono text-xs px-4 py-2 rounded-xl transition flex items-center space-x-1.5"
              >
                <Check className="w-4 h-4" />
                <span>Confirm Resolution & Close Task</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
