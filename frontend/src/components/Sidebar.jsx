import React from 'react';
import { 
  Send, 
  Search, 
  Wrench, 
  GitFork, 
  BarChart3, 
  Cpu, 
  ShieldCheck, 
  Radio, 
  AlertTriangle 
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab, currentUser, setCurrentUser }) => {
  const menuItems = [
    { id: 'submit', label: 'Submit Fault Report', icon: Send, badge: 'DFA Active' },
    { id: 'user', label: 'Track Reports', icon: Search },
    { id: 'handler', label: 'Handler Operations', icon: Wrench, badge: 'Tech View' },
    { id: 'routing', label: 'Routing Matrix', icon: GitFork, badge: 'Dispatch' },
    { id: 'analytics', label: 'System Analytics', icon: BarChart3, badge: 'Live DB' },
    { id: 'dfa', label: 'DFA Visualizer', icon: Cpu, badge: 'State Machine' }
  ];

  const demoRoles = [
    { role: 'admin', label: 'Administrator', username: 'admin' },
    { role: 'handler', label: 'Alex Carter (H1)', username: 'handler1' },
    { role: 'reporter', label: 'Officer Reed', username: 'reporter' }
  ];

  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-700 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Radio className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <h1 className="font-extrabold text-slate-100 text-base tracking-tight leading-none">
              TRAFFIC<span className="text-emerald-400">DISPATCH</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono tracking-wider mt-1 uppercase">
              Operations Control
            </p>
          </div>
        </div>
      </div>

      {/* System Status Pill */}
      <div className="px-5 py-3 bg-slate-950/50 border-b border-slate-800/80">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="text-xs font-mono text-emerald-400 font-semibold tracking-wide">SYSTEM ONLINE</span>
          </div>
          <span className="text-[11px] font-mono text-slate-500">v1.0.0</span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 px-3 py-1 font-semibold">
          Console Navigation
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md ${
                  isActive ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Role Switcher for Testing/Demo */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-mono text-slate-400 uppercase font-semibold">Demo Role Switcher</span>
          <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
        </div>
        <div className="grid grid-cols-3 gap-1.5">
          {demoRoles.map((r) => (
            <button
              key={r.role}
              onClick={() => setCurrentUser(r)}
              className={`text-[11px] py-1.5 px-1 rounded-lg font-mono transition-all text-center ${
                currentUser.role === r.role
                  ? 'bg-emerald-600 text-white font-bold shadow-sm shadow-emerald-900'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
              }`}
            >
              {r.role.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span className="truncate">Signed in: <strong className="text-slate-200">{currentUser.label}</strong></span>
        </div>
      </div>
    </aside>
  );
};
