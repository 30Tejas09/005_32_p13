import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { 
  BarChart3, 
  TrendingUp, 
  PieChart as PieIcon, 
  Users, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw,
  Activity,
  Layers
} from 'lucide-react';

export const AnalyticsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [zoneData, setZoneData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [priorityData, setPriorityData] = useState([]);
  const [handlerData, setHandlerData] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [mRes, zRes, cRes, pRes, hRes, aRes] = await Promise.all([
        api.getDashboardAnalytics(),
        api.getZoneDistribution(),
        api.getCategoryDistribution(),
        api.getPriorityDistribution(),
        api.getHandlerWorkload(),
        api.getRecentActivity()
      ]);
      setMetrics(mRes.metrics || {});
      setZoneData(zRes.zone_distribution || []);
      setCategoryData(cRes.category_distribution || []);
      setPriorityData(pRes.priority_distribution || []);
      setHandlerData(hRes.handler_workload || []);
      setRecentActivity(aRes.recent_activity || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  // Visual Palette
  const COLORS = ['#10B981', '#06B6D4', '#F59E0B', '#8B5CF6', '#EF4444'];
  const STATUS_COLORS = {
    Resolved: '#10B981',
    Active: '#06B6D4',
    Pending: '#F59E0B',
    Escalated: '#EF4444'
  };

  const statusPieData = metrics ? [
    { name: 'Resolved', value: metrics.resolved_reports },
    { name: 'In Progress / Assigned', value: metrics.assigned_reports + metrics.in_progress_reports },
    { name: 'Pending Queue', value: metrics.pending_reports },
    { name: 'Escalated', value: metrics.escalated_reports }
  ].filter(d => d.value > 0) : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-emerald-400" />
            Control Operations & Database Analytics
          </h2>
          <p className="text-sm text-slate-400">
            Real-time visual telemetry calculated directly from the SQLite database.
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-4 py-2 rounded-xl text-xs font-mono text-slate-300 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Sync Analytics</span>
        </button>
      </div>

      {/* Primary KPI Metrics Summary */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Total Reports</span>
            <span className="text-2xl font-black text-slate-100 font-mono mt-1 block">{metrics.total_reports}</span>
            <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Logged in SQLite</span>
          </div>
          <div className="bg-slate-900 border border-emerald-900/50 p-4 rounded-xl shadow-lg">
            <span className="text-[10px] font-mono uppercase text-emerald-400 block">Resolution Rate</span>
            <span className="text-2xl font-black text-emerald-300 font-mono mt-1 block">{metrics.resolution_rate}%</span>
            <span className="text-[10px] text-emerald-500 font-mono mt-0.5 block">{metrics.resolved_reports} resolved</span>
          </div>
          <div className="bg-slate-900 border border-cyan-900/50 p-4 rounded-xl shadow-lg">
            <span className="text-[10px] font-mono uppercase text-cyan-400 block">Active Handling</span>
            <span className="text-2xl font-black text-cyan-300 font-mono mt-1 block">
              {metrics.assigned_reports + metrics.in_progress_reports}
            </span>
            <span className="text-[10px] text-cyan-500 font-mono mt-0.5 block">Onsite field tasks</span>
          </div>
          <div className="bg-slate-900 border border-amber-900/50 p-4 rounded-xl shadow-lg">
            <span className="text-[10px] font-mono uppercase text-amber-400 block">Waiting Queue</span>
            <span className="text-2xl font-black text-amber-300 font-mono mt-1 block">{metrics.pending_reports}</span>
            <span className="text-[10px] text-amber-500 font-mono mt-0.5 block">Awaiting handlers</span>
          </div>
          <div className="bg-slate-900 border border-red-900/50 p-4 rounded-xl shadow-lg">
            <span className="text-[10px] font-mono uppercase text-red-400 block">Escalated</span>
            <span className="text-2xl font-black text-red-300 font-mono mt-1 block">{metrics.escalated_reports}</span>
            <span className="text-[10px] text-red-500 font-mono mt-0.5 block">Critical overrides</span>
          </div>
          <div className="bg-slate-900 border border-purple-900/50 p-4 rounded-xl shadow-lg">
            <span className="text-[10px] font-mono uppercase text-purple-400 block">Fleet Capacity</span>
            <span className="text-2xl font-black text-purple-300 font-mono mt-1 block">
              {metrics.total_workload} / {metrics.total_capacity}
            </span>
            <span className="text-[10px] text-purple-400 font-mono mt-0.5 block">{metrics.fleet_utilization}% utilized</span>
          </div>
        </div>
      )}

      {/* Row 1 Charts: Zone Distribution & Status Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Zone-Wise Fault Distribution Bar Chart (7 cols) */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-sm font-mono uppercase text-slate-200 font-bold flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" />
              Zone-Wise Fault Distribution (Active vs Resolved)
            </h3>
            <span className="text-[10px] font-mono text-slate-500">5 Geographic Zones</span>
          </div>
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="zone_code" stroke="#9ca3af" fontSize={11} fontFamily="JetBrains Mono" />
                <YAxis stroke="#9ca3af" fontSize={11} fontFamily="JetBrains Mono" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#374151', borderRadius: '12px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                <Bar dataKey="active" name="Active / Pending" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                <Bar dataKey="resolved" name="Resolved" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Distribution Donut Chart (5 cols) */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-sm font-mono uppercase text-slate-200 font-bold flex items-center gap-2">
              <PieIcon className="w-4 h-4 text-cyan-400" />
              Report Status Breakdown
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Live Status Ratio</span>
          </div>
          <div className="h-72 w-full flex items-center justify-center">
            {statusPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {statusPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#374151', borderRadius: '12px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-xs text-slate-500 font-mono">No data</span>
            )}
          </div>
        </div>
      </div>

      {/* Row 2 Charts: Category Distribution & Handler Workload */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Category Breakdown (6 cols) */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-sm font-mono uppercase text-slate-200 font-bold flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              Category-Wise Fault Distribution (Exact 5 Categories)
            </h3>
          </div>
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={categoryData} margin={{ top: 10, right: 20, left: 40, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
                <XAxis type="number" stroke="#9ca3af" fontSize={11} fontFamily="JetBrains Mono" />
                <YAxis dataKey="category" type="category" stroke="#9ca3af" fontSize={10} width={130} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#374151', borderRadius: '12px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                />
                <Bar dataKey="count" name="Fault Count" fill="#F59E0B" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Handler Workload Capacity Distribution (6 cols) */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-sm font-mono uppercase text-slate-200 font-bold flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" />
              Handler Workload vs Maximum Capacity
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Fleet Monitoring</span>
          </div>
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={handlerData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="handler_code" stroke="#9ca3af" fontSize={11} fontFamily="JetBrains Mono" />
                <YAxis stroke="#9ca3af" fontSize={11} fontFamily="JetBrains Mono" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#374151', borderRadius: '12px', fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
                <Bar dataKey="workload" name="Current Workload" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="capacity" name="Max Capacity" fill="#374151" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 3: Priority Distribution & Live Audit Log */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Priority breakdown cards */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <h3 className="text-sm font-mono uppercase text-slate-200 font-bold pb-2 border-b border-slate-800">
            Priority Distribution Breakdown
          </h3>
          <div className="space-y-2 font-mono text-xs">
            {priorityData.map((p) => (
              <div key={p.priority} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex items-center justify-between">
                <span className={`font-semibold ${
                  p.priority === 'EMERGENCY' ? 'text-red-400' :
                  p.priority === 'CRITICAL' ? 'text-orange-400' :
                  p.priority === 'HIGH' ? 'text-amber-400' :
                  p.priority === 'MEDIUM' ? 'text-yellow-400' : 'text-slate-400'
                }`}>
                  {p.priority}
                </span>
                <span className="bg-slate-800 px-2 py-0.5 rounded font-bold text-slate-200">
                  {p.count} reports
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Live System Activity Feed (8 cols) */}
        <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-sm font-mono uppercase text-slate-200 font-bold flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Live Status Activity History
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Latest 15 DB Events</span>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {recentActivity.map((act) => (
              <div
                key={act.id}
                className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 flex items-center justify-between text-xs font-mono"
              >
                <div className="flex items-center space-x-2 truncate max-w-lg">
                  <span className="font-bold text-cyan-400">{act.report_code}</span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-300 font-sans truncate">{act.remarks}</span>
                </div>
                <div className="flex items-center space-x-2 shrink-0">
                  <span className="text-emerald-400 font-bold">{act.new_status}</span>
                  <span className="text-slate-500 text-[10px]">{act.timestamp?.slice(11, 19)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
