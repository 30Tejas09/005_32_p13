import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ReportSubmission } from './pages/ReportSubmission';
import { UserDashboard } from './dashboards/UserDashboard';
import { HandlerDashboard } from './dashboards/HandlerDashboard';
import { RoutingDashboard } from './dashboards/RoutingDashboard';
import { AnalyticsDashboard } from './dashboards/AnalyticsDashboard';
import { DfaVisualizer } from './pages/DfaVisualizer';
import { Bell, Radio, Shield, Terminal } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('submit');
  const [currentUser, setCurrentUser] = useState({
    role: 'admin',
    label: 'System Administrator',
    username: 'admin'
  });
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 5000);
  };

  const handleReportSubmitted = (res) => {
    showToast(`Report ${res.report?.report_code} successfully submitted & routed (${res.dispatch_decision?.decision})!`);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-950">
      {/* Sidebar Left */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        setCurrentUser={setCurrentUser}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 bg-slate-900/90 backdrop-blur border-b border-slate-800 px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Active Console // <strong className="text-emerald-400">{activeTab.toUpperCase()}</strong>
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl text-xs font-mono">
              <span className="text-slate-500">ROLE:</span>
              <span className="text-emerald-400 font-bold uppercase">{currentUser.role}</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-300">{currentUser.label}</span>
            </div>

            <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl text-xs font-mono text-cyan-400">
              <Terminal className="w-3.5 h-3.5" />
              <span>DFA-READY</span>
            </div>
          </div>
        </header>

        {/* Dynamic Page Container */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          {/* Notification Toast */}
          {toast && (
            <div className="fixed bottom-6 right-6 z-50 bg-emerald-950 border border-emerald-500 text-emerald-300 px-5 py-3 rounded-2xl shadow-2xl font-mono text-xs flex items-center space-x-3 animate-bounce">
              <Radio className="w-4 h-4 text-emerald-400 animate-ping" />
              <span>{toast.msg}</span>
            </div>
          )}

          {activeTab === 'submit' && (
            <ReportSubmission onSubmitted={handleReportSubmitted} />
          )}
          {activeTab === 'user' && (
            <UserDashboard />
          )}
          {activeTab === 'handler' && (
            <HandlerDashboard currentUser={currentUser} />
          )}
          {activeTab === 'routing' && (
            <RoutingDashboard />
          )}
          {activeTab === 'analytics' && (
            <AnalyticsDashboard />
          )}
          {activeTab === 'dfa' && (
            <DfaVisualizer />
          )}
        </main>
      </div>
    </div>
  );
}
