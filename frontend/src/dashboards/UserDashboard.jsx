import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { StatusBadge, PriorityBadge, CategoryBadge } from '../components/StatusBadge';
import { 
  Search, 
  Filter, 
  Clock, 
  MapPin, 
  CheckCircle2, 
  AlertTriangle, 
  Eye, 
  X, 
  RefreshCw,
  FileText,
  User,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export const UserDashboard = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportDetails, setReportDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const data = await api.getReports({
        q: searchTerm,
        status: statusFilter,
        priority: priorityFilter
      });
      setReports(data.reports || []);
    } catch (err) {
      console.error('Error fetching reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [statusFilter, priorityFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchReports();
  };

  const handleOpenDetails = async (rep) => {
    setSelectedReport(rep);
    setLoadingDetails(true);
    try {
      const full = await api.getReportById(rep.id);
      setReportDetails(full);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  // Metrics count
  const metrics = {
    total: reports.length,
    pending: reports.filter(r => r.status === 'PENDING').length,
    assigned: reports.filter(r => r.status === 'ASSIGNED').length,
    inProgress: reports.filter(r => r.status === 'IN_PROGRESS').length,
    resolved: reports.filter(r => r.status === 'RESOLVED').length
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title & Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-100 tracking-tight">
            Traffic Fault Tracker & Citizen Dashboard
          </h2>
          <p className="text-sm text-slate-400">
            Real-time status tracking, handler dispatch audit history, and resolution tracking.
          </p>
        </div>
        <button
          onClick={fetchReports}
          className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-4 py-2 rounded-xl text-xs font-mono text-slate-300 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Refresh Database</span>
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">Total Reports</span>
          <span className="text-2xl font-black text-slate-100 font-mono mt-1 block">{metrics.total}</span>
        </div>
        <div className="bg-slate-900 border border-amber-900/40 p-4 rounded-xl shadow-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 block">Pending Queue</span>
          <span className="text-2xl font-black text-amber-300 font-mono mt-1 block">{metrics.pending}</span>
        </div>
        <div className="bg-slate-900 border border-cyan-900/40 p-4 rounded-xl shadow-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 block">Assigned</span>
          <span className="text-2xl font-black text-cyan-300 font-mono mt-1 block">{metrics.assigned}</span>
        </div>
        <div className="bg-slate-900 border border-blue-900/40 p-4 rounded-xl shadow-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-blue-400 block">In Progress</span>
          <span className="text-2xl font-black text-blue-300 font-mono mt-1 block">{metrics.inProgress}</span>
        </div>
        <div className="bg-slate-900 border border-emerald-900/40 p-4 rounded-xl shadow-lg">
          <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 block">Resolved</span>
          <span className="text-2xl font-black text-emerald-300 font-mono mt-1 block">{metrics.resolved}</span>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-xl flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search report ID, signal, location..."
            className="w-full bg-slate-950 border border-slate-800 pl-10 pr-4 py-2 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition font-mono"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 px-3 py-2 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
          >
            <option value="">All Statuses</option>
            <option value="SUBMITTED">SUBMITTED</option>
            <option value="PENDING">PENDING</option>
            <option value="ASSIGNED">ASSIGNED</option>
            <option value="IN_PROGRESS">IN_PROGRESS</option>
            <option value="ESCALATED">ESCALATED</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 px-3 py-2 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
          >
            <option value="">All Priorities</option>
            <option value="EMERGENCY">EMERGENCY</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 font-mono flex items-center justify-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
            <span>Loading database records...</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="p-12 text-center text-slate-500 font-mono">
            No matching reports found in database.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-950 border-b border-slate-800 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4 font-semibold">Report ID</th>
                  <th className="py-3.5 px-4 font-semibold">Signal / Location</th>
                  <th className="py-3.5 px-4 font-semibold">Category</th>
                  <th className="py-3.5 px-4 font-semibold">Priority</th>
                  <th className="py-3.5 px-4 font-semibold">Status</th>
                  <th className="py-3.5 px-4 font-semibold">Assigned Handler</th>
                  <th className="py-3.5 px-4 font-semibold">Submitted</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {reports.map((rep) => (
                  <tr 
                    key={rep.id} 
                    className="hover:bg-slate-800/40 transition cursor-pointer"
                    onClick={() => handleOpenDetails(rep)}
                  >
                    <td className="py-3.5 px-4 font-bold text-cyan-400">
                      {rep.report_code}
                    </td>
                    <td className="py-3.5 px-4 font-sans">
                      <div className="font-semibold text-slate-200">{rep.signal_id}</div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-1 truncate max-w-xs">
                        <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                        <span className="truncate">{rep.location}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-sans">
                      <CategoryBadge category={rep.category} />
                    </td>
                    <td className="py-3.5 px-4">
                      <PriorityBadge priority={rep.priority} />
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={rep.status} />
                    </td>
                    <td className="py-3.5 px-4 font-sans">
                      {rep.active_assignment?.handler_name ? (
                        <div className="text-slate-300 font-medium">
                          {rep.active_assignment.handler_name}
                        </div>
                      ) : (
                        <span className="text-slate-500 italic text-[11px]">Unassigned (Queue)</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {rep.created_at?.slice(0, 16).replace('T', ' ')}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDetails(rep);
                        }}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-300 p-1.5 rounded-lg border border-slate-700 transition"
                      >
                        <Eye className="w-4 h-4 text-cyan-400" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Report Details Drawer / Modal */}
      {selectedReport && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-3xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center">
                  <FileText className="w-4 h-4 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold font-mono text-slate-100">
                    {selectedReport.report_code}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Signal: <span className="text-slate-200 font-mono font-semibold">{selectedReport.signal_id}</span> ({selectedReport.zone_code})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedReport(null)}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-xl hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs font-mono">
              {loadingDetails ? (
                <div className="py-12 text-center text-slate-400 flex items-center justify-center space-x-2">
                  <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
                  <span>Loading full report relations...</span>
                </div>
              ) : reportDetails ? (
                <>
                  {/* Status & Priority Overview Bar */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase block">Status</span>
                      <StatusBadge status={reportDetails.status} />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase block">Priority</span>
                      <PriorityBadge priority={reportDetails.priority} />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase block">Assigned Handler</span>
                      <span className="text-slate-200 font-bold block truncate mt-1">
                        {reportDetails.active_assignment?.handler_name || 'In Waiting Queue'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase block">Reported By</span>
                      <span className="text-slate-300 font-bold block truncate mt-1">
                        {reportDetails.reporter_name}
                      </span>
                    </div>
                  </div>

                  {/* Description Box */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1 font-sans">
                    <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
                      Fault Description & Classification
                    </span>
                    <p className="text-sm text-slate-200 leading-relaxed">
                      {reportDetails.description}
                    </p>
                    <div className="pt-2 flex items-center space-x-2">
                      <CategoryBadge category={reportDetails.category} />
                    </div>
                  </div>

                  {/* Status History Timeline */}
                  <div className="space-y-3">
                    <span className="text-[11px] font-mono uppercase text-slate-400 font-bold flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-cyan-400" />
                      Status Transition Audit History
                    </span>
                    <div className="space-y-2 border-l-2 border-slate-800 pl-4 ml-2">
                      {reportDetails.history?.map((h) => (
                        <div key={h.id} className="relative pb-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 absolute -left-[21px] top-1 border-2 border-slate-950"></span>
                          <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-1 text-[11px]">
                            <div>
                              <span className="font-bold text-slate-200">
                                {h.previous_status ? `${h.previous_status} → ` : 'INITIAL → '} 
                                <span className="text-emerald-400">{h.new_status}</span>
                              </span>
                              <span className="text-slate-400 block text-[10px] mt-0.5">
                                Updated by <strong className="text-slate-300">{h.updated_by}</strong>: {h.remarks || 'No remarks'}
                              </span>
                            </div>
                            <span className="text-slate-500 text-[10px]">
                              {h.created_at?.slice(0, 19).replace('T', ' ')}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Dispatch Logs */}
                  {reportDetails.dispatch_logs?.length > 0 && (
                    <div className="space-y-2">
                      <span className="text-[11px] font-mono uppercase text-slate-400 font-bold flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        Dispatch Engine Decision Record
                      </span>
                      {reportDetails.dispatch_logs.map((dl) => (
                        <div key={dl.id} className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-[11px]">
                          <div className="flex items-center justify-between text-emerald-400 font-bold mb-1">
                            <span>{dl.decision}</span>
                            <span className="text-slate-500 text-[10px] font-normal">{dl.timestamp?.slice(0, 19).replace('T', ' ')}</span>
                          </div>
                          <p className="text-slate-300 font-sans text-xs">{dl.reason}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-slate-950 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedReport(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs px-4 py-2 rounded-xl transition"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
