import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { StatusBadge, PriorityBadge, CategoryBadge } from '../components/StatusBadge';
import { 
  GitFork, 
  Layers, 
  AlertOctagon, 
  ArrowRight, 
  Send, 
  Edit2, 
  Save, 
  X, 
  RefreshCw, 
  ShieldAlert,
  Clock,
  CheckCircle,
  HelpCircle
} from 'lucide-react';

export const RoutingDashboard = () => {
  const [rules, setRules] = useState([]);
  const [zones, setZones] = useState([]);
  const [handlers, setHandlers] = useState([]);
  const [waitingQueue, setWaitingQueue] = useState([]);
  const [dispatchLogs, setDispatchLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingRule, setEditingRule] = useState(null);
  const [selectedZoneTab, setSelectedZoneTab] = useState('ALL');
  const [activeTabSub, setActiveTabSub] = useState('matrix'); // 'matrix', 'queue', 'logs'

  const loadData = async () => {
    setLoading(true);
    try {
      const [rRes, zRes, hRes, qRes, lRes] = await Promise.all([
        api.getRoutingRules(),
        api.getZones(),
        api.getHandlers(),
        api.getWaitingQueue(),
        api.getDispatchLogs()
      ]);
      setRules(rRes.rules || []);
      setZones(zRes.zones || []);
      setHandlers(hRes.handlers || []);
      setWaitingQueue(qRes.queue || []);
      setDispatchLogs(lRes.logs || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTriggerDispatch = async (reportId) => {
    try {
      await api.triggerDispatch(reportId, 'ADMIN_MANUAL_DISPATCH');
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveRule = async () => {
    if (!editingRule) return;
    try {
      await api.updateRoutingRule(editingRule.id, {
        primary_handler_id: editingRule.primary_handler_id,
        backup_handler_id: editingRule.backup_handler_id,
        escalation_path: editingRule.escalation_path
      });
      setEditingRule(null);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredRules = selectedZoneTab === 'ALL'
    ? rules
    : rules.filter(r => r.zone_code === selectedZoneTab);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
            <GitFork className="w-6 h-6 text-emerald-400" />
            Routing Table & Automated Dispatch Matrix
          </h2>
          <p className="text-sm text-slate-400">
            Zone-based primary, backup handler assignments, emergency escalation paths, and waiting queues.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTabSub('matrix')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition ${
              activeTabSub === 'matrix' ? 'bg-emerald-500 text-slate-950' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
            }`}
          >
            Routing Matrix ({rules.length})
          </button>
          <button
            onClick={() => setActiveTabSub('queue')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition flex items-center space-x-1.5 ${
              activeTabSub === 'queue' ? 'bg-amber-500 text-slate-950' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
            }`}
          >
            <span>Waiting Queue</span>
            {waitingQueue.length > 0 && (
              <span className="bg-slate-950 text-amber-300 text-[10px] px-1.5 rounded-full font-mono">
                {waitingQueue.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTabSub('logs')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition ${
              activeTabSub === 'logs' ? 'bg-cyan-500 text-slate-950' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
            }`}
          >
            Audit Logs
          </button>
          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Sub-Tab View */}
      {activeTabSub === 'matrix' && (
        <div className="space-y-4">
          {/* Zone Selector Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-900 p-1.5 rounded-xl border border-slate-800 w-fit">
            <button
              onClick={() => setSelectedZoneTab('ALL')}
              className={`px-3 py-1 rounded-lg text-xs font-mono transition ${
                selectedZoneTab === 'ALL' ? 'bg-emerald-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ALL ZONES
            </button>
            {zones.map((z) => (
              <button
                key={z.id}
                onClick={() => setSelectedZoneTab(z.zone_code)}
                className={`px-3 py-1 rounded-lg text-xs font-mono transition ${
                  selectedZoneTab === z.zone_code ? 'bg-emerald-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {z.zone_code}
              </button>
            ))}
          </div>

          {/* Rules Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-950 border-b border-slate-800 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                    <th className="py-3.5 px-4 font-semibold">Zone</th>
                    <th className="py-3.5 px-4 font-semibold">Fault Category</th>
                    <th className="py-3.5 px-4 font-semibold">Primary Handler</th>
                    <th className="py-3.5 px-4 font-semibold">Backup Handler</th>
                    <th className="py-3.5 px-4 font-semibold">Escalation Path</th>
                    <th className="py-3.5 px-4 font-semibold text-right">Configure</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredRules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4 font-bold text-cyan-400">
                        {rule.zone_code}
                      </td>
                      <td className="py-3.5 px-4 font-sans">
                        <CategoryBadge category={rule.category} />
                      </td>
                      <td className="py-3.5 px-4 font-sans font-semibold text-emerald-400">
                        {rule.primary_handler_name}
                      </td>
                      <td className="py-3.5 px-4 font-sans text-amber-300">
                        {rule.backup_handler_name}
                      </td>
                      <td className="py-3.5 px-4 text-rose-400 text-[11px]">
                        {rule.escalation_path}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => setEditingRule(rule)}
                          className="bg-slate-800 hover:bg-slate-700 text-slate-300 p-1.5 rounded-lg border border-slate-700 transition"
                        >
                          <Edit2 className="w-3.5 h-3.5 text-cyan-400" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Waiting Queue Sub-Tab */}
      {activeTabSub === 'queue' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>Deterministic Waiting Queue</span>
                <span className="text-xs font-mono bg-amber-950 text-amber-400 px-2 py-0.5 rounded border border-amber-800">
                  Priority-Sorted (Emergency → Critical → High → Med → Low)
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Reports waiting for handler availability or capacity clearance. Tie-breaking by earliest submission time.
              </p>
            </div>
          </div>

          {waitingQueue.length === 0 ? (
            <div className="py-12 text-center text-slate-500 font-mono">
              Waiting queue is currently empty. All incoming reports have been assigned or resolved!
            </div>
          ) : (
            <div className="space-y-3">
              {waitingQueue.map((rep, idx) => (
                <div
                  key={rep.id}
                  className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="flex items-start space-x-3">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-slate-400 font-mono text-xs flex items-center justify-center font-bold">
                      #{idx + 1}
                    </span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-cyan-400 text-sm">{rep.report_code}</span>
                        <PriorityBadge priority={rep.priority} />
                        <StatusBadge status={rep.status} />
                      </div>
                      <p className="text-xs text-slate-300 font-sans mt-1">
                        {rep.description}
                      </p>
                      <div className="text-[11px] font-mono text-slate-500 mt-1">
                        Zone: <strong className="text-slate-300">{rep.zone_code || rep.zone_raw}</strong> • Submitted: {rep.created_at?.slice(0, 19).replace('T', ' ')}
                      </div>
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center space-x-2">
                    <button
                      onClick={() => handleTriggerDispatch(rep.id)}
                      className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold font-mono text-xs px-4 py-2 rounded-xl transition flex items-center space-x-1.5"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>Re-Dispatch</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Audit Logs Sub-Tab */}
      {activeTabSub === 'logs' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-cyan-400" />
              Dispatch Decision Records
            </h3>
            <span className="text-xs font-mono text-slate-500">Live Decision Feed</span>
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {dispatchLogs.map((log) => (
              <div
                key={log.id}
                className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs font-mono space-y-1"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-cyan-400">{log.report_code || `Report #${log.report_id}`}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      log.decision.includes('PRIMARY') ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                      log.decision.includes('BACKUP') ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                      log.decision.includes('ESCALATED') ? 'bg-red-950 text-red-400 border border-red-800' :
                      'bg-slate-900 text-slate-400 border border-slate-700'
                    }`}>
                      {log.decision}
                    </span>
                  </div>
                  <span className="text-slate-500 text-[10px]">{log.timestamp?.slice(0, 19).replace('T', ' ')}</span>
                </div>
                <p className="text-slate-300 font-sans text-xs pt-1">{log.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Edit Rule Modal */}
      {editingRule && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Edit2 className="w-5 h-5 text-cyan-400" />
                Configure Rule: {editingRule.zone_code} - {editingRule.category}
              </h3>
              <button onClick={() => setEditingRule(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-400 mb-1">PRIMARY HANDLER *</label>
                <select
                  value={editingRule.primary_handler_id}
                  onChange={(e) => setEditingRule({ ...editingRule, primary_handler_id: Number(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded-xl text-slate-100"
                >
                  {handlers.map(h => (
                    <option key={h.id} value={h.id}>{h.handler_code} - {h.name} ({h.zone_code})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">BACKUP HANDLER</label>
                <select
                  value={editingRule.backup_handler_id || ''}
                  onChange={(e) => setEditingRule({ ...editingRule, backup_handler_id: e.target.value ? Number(e.target.value) : null })}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded-xl text-slate-100"
                >
                  <option value="">None Configured</option>
                  {handlers.map(h => (
                    <option key={h.id} value={h.id}>{h.handler_code} - {h.name} ({h.zone_code})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">ESCALATION PATH</label>
                <input
                  type="text"
                  value={editingRule.escalation_path}
                  onChange={(e) => setEditingRule({ ...editingRule, escalation_path: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded-xl text-slate-100"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => setEditingRule(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs px-4 py-2 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRule}
                className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold font-mono text-xs px-4 py-2 rounded-xl transition flex items-center space-x-1.5"
              >
                <Save className="w-4 h-4" />
                <span>Save Routing Configuration</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
