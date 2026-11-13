import React from 'react';

export const StatusBadge = ({ status }) => {
  const getStyle = (s) => {
    switch (s?.toUpperCase()) {
      case 'RESOLVED':
        return 'bg-emerald-950/80 text-emerald-400 border-emerald-500/40';
      case 'IN_PROGRESS':
        return 'bg-blue-950/80 text-blue-400 border-blue-500/40 animate-pulse';
      case 'ASSIGNED':
        return 'bg-cyan-950/80 text-cyan-400 border-cyan-500/40';
      case 'PENDING':
        return 'bg-amber-950/80 text-amber-400 border-amber-500/40';
      case 'ESCALATED':
        return 'bg-rose-950/80 text-rose-400 border-rose-500/50 font-bold';
      case 'SUBMITTED':
      case 'VALIDATING':
        return 'bg-slate-800 text-slate-300 border-slate-600';
      case 'REJECTED':
        return 'bg-red-950/90 text-red-400 border-red-600/50 line-through';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${getStyle(status)}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-75"></span>
      {status || 'UNKNOWN'}
    </span>
  );
};

export const PriorityBadge = ({ priority }) => {
  const getStyle = (p) => {
    switch (p?.toUpperCase()) {
      case 'EMERGENCY':
        return 'bg-red-950 text-red-400 border-red-500 shadow-sm shadow-red-900/50 font-bold';
      case 'CRITICAL':
        return 'bg-orange-950 text-orange-400 border-orange-500 font-semibold';
      case 'HIGH':
        return 'bg-amber-950/80 text-amber-300 border-amber-500/50';
      case 'MEDIUM':
        return 'bg-yellow-950/60 text-yellow-400 border-yellow-500/30';
      case 'LOW':
        return 'bg-slate-800/80 text-slate-400 border-slate-700';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold uppercase border ${getStyle(priority)}`}>
      {priority === 'EMERGENCY' && <span className="mr-1">🚨</span>}
      {priority === 'CRITICAL' && <span className="mr-1">⚠️</span>}
      {priority || 'NORMAL'}
    </span>
  );
};

export const CategoryBadge = ({ category }) => {
  const getIcon = (cat) => {
    if (cat?.includes('Light')) return '🚦';
    if (cat?.includes('Timing')) return '⏱️';
    if (cat?.includes('Electrical') || cat?.includes('Controller')) return '⚡';
    if (cat?.includes('Sensor')) return '📡';
    if (cat?.includes('Communication') || cat?.includes('Network')) return '🌐';
    return '🔧';
  };

  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800/90 text-slate-200 border border-slate-700">
      <span className="mr-1.5 text-sm">{getIcon(category)}</span>
      <span className="truncate max-w-[200px]">{category}</span>
    </span>
  );
};
