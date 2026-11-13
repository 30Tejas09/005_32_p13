import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  Cpu, 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  FileCode, 
  Info,
  ChevronRight,
  StepForward
} from 'lucide-react';

export const DfaVisualizer = () => {
  const [testInput, setTestInput] = useState('TSF-2026-00001');
  const [simulation, setSimulation] = useState(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [dfaMetadata, setDfaMetadata] = useState(null);

  useEffect(() => {
    api.getDFAInfo().then(res => setDfaMetadata(res.formal_definition)).catch(() => {});
    runSimulation('TSF-2026-00001');
  }, []);

  const runSimulation = async (inputStr) => {
    try {
      const res = await api.simulateDFA(inputStr);
      setSimulation(res);
      setCurrentStepIndex(res.steps?.length - 1);
    } catch (err) {
      console.error(err);
    }
  };

  const handleInputChange = (val) => {
    setTestInput(val);
    runSimulation(val);
  };

  const handlePreset = (str) => {
    setTestInput(str);
    runSimulation(str);
  };

  // Determine active state for highlighting
  const activeState = (simulation && currentStepIndex >= 0 && simulation.steps && simulation.steps[currentStepIndex])
    ? simulation.steps[currentStepIndex].to_state
    : 'q0';

  const isAccepted = simulation?.is_accepted;
  const isTrap = activeState === 'q_trap';

  const dfaNodes = [
    { id: 'q0', label: 'q0', desc: 'Start (T)' },
    { id: 'q1', label: 'q1', desc: 'Saw T' },
    { id: 'q2', label: 'q2', desc: 'Saw S' },
    { id: 'q3', label: 'q3', desc: 'Saw F' },
    { id: 'q4', label: 'q4', desc: 'Saw -' },
    { id: 'q5', label: 'q5', desc: 'Year Y1' },
    { id: 'q6', label: 'q6', desc: 'Year Y2' },
    { id: 'q7', label: 'q7', desc: 'Year Y3' },
    { id: 'q8', label: 'q8', desc: 'Year Y4' },
    { id: 'q9', label: 'q9', desc: 'Saw -' },
    { id: 'q10', label: 'q10', desc: 'Seq S1' },
    { id: 'q11', label: 'q11', desc: 'Seq S2' },
    { id: 'q12', label: 'q12', desc: 'Seq S3' },
    { id: 'q13', label: 'q13', desc: 'Seq S4' },
    { id: 'q14', label: 'q14', desc: 'ACCEPT (S5)' },
    { id: 'q_trap', label: 'TRAP', desc: 'REJECT' }
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-mono">
      {/* Top Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs text-cyan-400 uppercase tracking-wider mb-1 font-semibold">
            <Cpu className="w-4 h-4" />
            <span>Formal Language & Automata Theory Module</span>
          </div>
          <h2 className="text-2xl font-black text-slate-100 tracking-tight font-sans">
            Deterministic Finite Automaton (DFA) Simulator
          </h2>
          <p className="text-sm text-slate-400 font-sans mt-1">
            Validates Report Identifiers: <code className="text-cyan-400 bg-slate-950 px-2 py-0.5 rounded">TSF-YYYY-XXXXX</code> via formal 5-tuple <code className="text-emerald-400">M = (Q, Σ, δ, q0, F)</code>.
          </p>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl text-xs space-y-1">
          <div className="text-slate-400">Formal Definition:</div>
          <div className="text-slate-300">|Q| = 16 States • |Σ| = 14 Symbols • |F| = &#123; q14 &#125;</div>
        </div>
      </div>

      {/* Interactive Input & Presets */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="w-full md:flex-1">
            <label className="text-xs uppercase text-slate-400 block mb-1 font-semibold">
              Input String to Validate:
            </label>
            <input
              type="text"
              value={testInput}
              onChange={(e) => handleInputChange(e.target.value)}
              placeholder="e.g. TSF-2026-00001"
              className="w-full bg-slate-950 border border-slate-700 px-4 py-3 rounded-xl text-base tracking-widest text-slate-100 focus:outline-none focus:border-cyan-500 font-bold"
            />
          </div>

          {/* Stepper Controls */}
          {simulation && simulation.steps && (
            <div className="flex items-center space-x-2 shrink-0 pt-5">
              <button
                disabled={currentStepIndex <= 0}
                onClick={() => setCurrentStepIndex(prev => Math.max(0, prev - 1))}
                className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300 px-3 py-2 rounded-xl text-xs flex items-center space-x-1"
              >
                <span>Step -1</span>
              </button>
              <button
                disabled={currentStepIndex >= simulation.steps.length - 1}
                onClick={() => setCurrentStepIndex(prev => Math.min(simulation.steps.length - 1, prev + 1))}
                className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300 px-3 py-2 rounded-xl text-xs flex items-center space-x-1"
              >
                <span>Step +1</span>
              </button>
              <button
                onClick={() => setCurrentStepIndex(simulation.steps.length - 1)}
                className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-3 py-2 rounded-xl text-xs"
              >
                End
              </button>
            </div>
          )}
        </div>

        {/* Preset Test Case Buttons */}
        <div className="pt-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-500 font-sans text-xs">Test Scenarios:</span>
          <button
            onClick={() => handlePreset('TSF-2026-00001')}
            className="bg-slate-950 hover:bg-slate-800 border border-emerald-900/50 text-emerald-400 px-2.5 py-1 rounded-lg"
          >
            ✓ Valid ID
          </button>
          <button
            onClick={() => handlePreset('TXF-2026-00001')}
            className="bg-slate-950 hover:bg-slate-800 border border-red-900/50 text-red-400 px-2.5 py-1 rounded-lg"
          >
            ✗ Bad Prefix 'TXF'
          </button>
          <button
            onClick={() => handlePreset('TSF-202-00001')}
            className="bg-slate-950 hover:bg-slate-800 border border-red-900/50 text-red-400 px-2.5 py-1 rounded-lg"
          >
            ✗ 3-Digit Year
          </button>
          <button
            onClick={() => handlePreset('TSF-2026-000A1')}
            className="bg-slate-950 hover:bg-slate-800 border border-red-900/50 text-red-400 px-2.5 py-1 rounded-lg"
          >
            ✗ Letter in Sequence
          </button>
          <button
            onClick={() => handlePreset('TSF-2026-000001')}
            className="bg-slate-950 hover:bg-slate-800 border border-red-900/50 text-red-400 px-2.5 py-1 rounded-lg"
          >
            ✗ Overflow (15 chars)
          </button>
        </div>
      </div>

      {/* Live State Machine Visual Diagram */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <h3 className="text-sm uppercase text-slate-200 font-bold flex items-center gap-2">
            <span>DFA Transition Graph</span>
            <span className="text-xs text-cyan-400 font-normal">Active State: <strong className="text-cyan-300">{activeState}</strong></span>
          </h3>
          <span className="text-[10px] text-slate-500">Left-to-Right Linear Automaton</span>
        </div>

        {/* Visual Graph Nodes */}
        <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 overflow-x-auto">
          <div className="flex items-center space-x-2 min-w-[900px] py-4">
            {dfaNodes.map((node, index) => {
              const isCurrent = activeState === node.id;
              const isAccepting = node.id === 'q14';
              const isTrapNode = node.id === 'q_trap';

              return (
                <React.Fragment key={node.id}>
                  {isTrapNode && <div className="border-l border-dashed border-red-900 mx-2 h-12"></div>}
                  <div
                    className={`shrink-0 flex flex-col items-center justify-center transition-all duration-300 ${
                      isTrapNode ? 'ml-4' : ''
                    }`}
                  >
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                        isCurrent
                          ? isTrapNode
                            ? 'bg-red-500 text-white ring-4 ring-red-500/50 scale-110 shadow-lg shadow-red-500/50'
                            : isAccepting
                            ? 'bg-emerald-500 text-slate-950 ring-4 ring-emerald-500/50 scale-110 shadow-lg shadow-emerald-500/50'
                            : 'bg-cyan-500 text-slate-950 ring-4 ring-cyan-500/50 scale-110 shadow-lg shadow-cyan-500/50'
                          : isAccepting
                          ? 'bg-emerald-950/80 border-2 border-emerald-500 text-emerald-400'
                          : isTrapNode
                          ? 'bg-red-950/80 border border-red-700 text-red-400'
                          : 'bg-slate-900 border border-slate-800 text-slate-400'
                      }`}
                    >
                      {node.label}
                    </div>
                    <span className="text-[9px] text-slate-400 mt-1 text-center truncate w-14">
                      {node.desc}
                    </span>
                  </div>
                  {index < dfaNodes.length - 2 && (
                    <ArrowRight className="w-3.5 h-3.5 text-slate-700 shrink-0" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Validation Results Comparison: DFA vs Regex */}
      {simulation && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* DFA Result Card */}
          <div className={`p-5 rounded-2xl border shadow-xl ${
            simulation.is_accepted ? 'bg-emerald-950/20 border-emerald-500/50' : 'bg-red-950/20 border-red-500/50'
          }`}>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                {simulation.is_accepted ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-400" />
                )}
                <h4 className="font-bold text-sm text-slate-100">DFA Automaton Decision</h4>
              </div>
              <span className={`text-xs px-2.5 py-0.5 rounded font-bold ${
                simulation.is_accepted ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-red-950 text-red-400 border border-red-800'
              }`}>
                {simulation.is_accepted ? 'ACCEPTED' : 'REJECTED'}
              </span>
            </div>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Terminal State:</span>
                <span className="font-bold text-slate-200">{simulation.final_state}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Valid Transitions:</span>
                <span className="font-bold text-slate-200">{simulation.steps?.length} / 14</span>
              </div>
              {simulation.error_reason && (
                <div className="bg-red-950/80 p-2.5 rounded-xl border border-red-900/60 text-red-300 text-[11px] font-sans">
                  <strong>Rejection Cause:</strong> {simulation.error_reason}
                </div>
              )}
            </div>
          </div>

          {/* Regex Comparison Card */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <FileCode className="w-5 h-5 text-cyan-400" />
                <h4 className="font-bold text-sm text-slate-100">Regex Validation Parity</h4>
              </div>
              <span className={`text-xs px-2.5 py-0.5 rounded font-bold ${
                simulation.regex_match ? 'bg-cyan-950 text-cyan-400 border border-cyan-800' : 'bg-slate-800 text-slate-400'
              }`}>
                {simulation.regex_match ? 'REGEX MATCH' : 'NO MATCH'}
              </span>
            </div>
            <div className="space-y-2 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px]">EQUIVALENT PATTERN</span>
                <code className="text-cyan-300 bg-slate-950 p-1.5 rounded block text-[11px] border border-slate-800 mt-1">
                  {simulation.regex_pattern}
                </code>
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-slate-400">DFA & Regex Equivalence:</span>
                <span className={`font-bold ${simulation.equivalent ? 'text-emerald-400' : 'text-red-400'}`}>
                  {simulation.equivalent ? '✓ 100% IDENTICAL' : '✗ DISCREPANCY'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step Transition Trace Table */}
      {simulation && simulation.steps && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden p-6 space-y-3">
          <h3 className="text-sm uppercase text-slate-200 font-bold pb-2 border-b border-slate-800">
            Step-by-Step Transition Log (Simulation Trace)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 text-[11px]">
                  <th className="py-2.5 px-3">Step</th>
                  <th className="py-2.5 px-3">Input Symbol</th>
                  <th className="py-2.5 px-3">Source State</th>
                  <th className="py-2.5 px-3">Target State</th>
                  <th className="py-2.5 px-3">Transition Rule & Explanation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {simulation.steps.map((st, i) => (
                  <tr
                    key={st.step}
                    className={`transition ${
                      i === currentStepIndex ? 'bg-cyan-950/40 font-bold text-cyan-300' : 'text-slate-300'
                    }`}
                  >
                    <td className="py-2 px-3 text-slate-500">#{st.step}</td>
                    <td className="py-2 px-3">
                      <span className="bg-slate-800 text-cyan-400 px-2 py-0.5 rounded font-bold">
                        '{st.char}'
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400">{st.from_state}</td>
                    <td className="py-2 px-3 font-bold text-emerald-400">{st.to_state}</td>
                    <td className="py-2 px-3 font-sans text-slate-300 text-xs">{st.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
