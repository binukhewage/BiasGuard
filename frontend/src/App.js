import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, AlertTriangle, ShieldCheck, Server, Database } from 'lucide-react';


function App() {
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);

  // Poll the Backend API every 2 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/metrics');
        const data = res.data;
        setMetrics(data);
        
        // Add to history for the Line Chart
        setHistory(prev => {
          // Avoid duplicate rounds
          if (prev.length > 0 && prev[prev.length - 1].round === data.round) return prev;
          // Keep history length manageable (last 20 points)
          const newHist = [...prev, { round: `R${data.round}`, accuracy: (data.accuracy * 100).toFixed(1) }];
          return newHist.slice(-20); 
        });
      } catch (err) {
        console.error("Backend offline");
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return (
    <div className="flex h-screen items-center justify-center bg-slate-900 text-emerald-400 animate-pulse font-mono">
      Connecting to BiasGuard Server...
    </div>
  );

  const isBiasAlert = metrics.clients["Hospital B"] > 0.15;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-6 font-sans selection:bg-emerald-500 selection:text-white">
      <div className="max-w-7xl mx-auto">
        
        {/* HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-center mb-8 border-b border-slate-800 pb-6 pt-5">
          <div className="flex items-center gap-4 mb-4 md:mb-0">
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-700 shadow-lg shadow-emerald-500/10">
              <ShieldCheck size={32} className="text-emerald-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">BiasGuard</h1>
              <p className="text-slate-400 text-sm font-medium">Federated ICU Analytics Framework</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-full border border-slate-800">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-emerald-400 font-bold text-xs tracking-wider">LIVE AGGREGATION</span>
          </div>
        </header>

        {/* MAIN GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* LEFT COLUMN */}
          <div className="space-y-6">
            
            {/* Global Accuracy Card */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Activity size={100} />
              </div>
              <div className="flex items-center gap-3 mb-2 text-slate-400 uppercase text-xs font-bold tracking-widest">
                <Activity size={16} /> Global Model Accuracy
              </div>
              <div className="text-5xl font-black text-white mb-6">
                {(metrics.accuracy * 100).toFixed(1)}<span className="text-2xl text-emerald-500">%</span>
              </div>
              <div className="h-40 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                    <XAxis dataKey="round" stroke="#64748b" tick={{fontSize: 12}} />
                    <YAxis domain={[50, 100]} stroke="#64748b" tick={{fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc'}} 
                      itemStyle={{color: '#4ade80'}}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="accuracy" 
                      stroke="#4ade80" 
                      strokeWidth={3} 
                      dot={{r: 4, fill: '#0f172a', strokeWidth: 2}} 
                      activeDot={{r: 6}}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Bias Alert Card (Dynamic) */}
            <div className={`rounded-xl border p-6 shadow-xl transition-all duration-500 ${
              isBiasAlert 
                ? 'bg-gradient-to-br from-red-950 to-slate-900 border-red-500/50 shadow-red-900/20' 
                : 'bg-slate-900 border-slate-800'
            }`}>
              <div className="flex items-center gap-3 mb-4 text-slate-400 uppercase text-xs font-bold tracking-widest">
                <AlertTriangle size={16} className={isBiasAlert ? "text-red-500 animate-bounce" : "text-yellow-500"} /> 
                Real-Time Bias Monitor
              </div>
              
              {isBiasAlert ? (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <h2 className="text-2xl font-bold text-white mb-1">CRITICAL BIAS DETECTED</h2>
                  <div className="flex flex-col gap-2 mt-4">
                    <div className="flex justify-between text-sm border-b border-red-900/50 pb-2">
                      <span className="text-red-200">Triggering Node:</span>
                      <span className="font-mono font-bold text-red-400">Hospital B</span>
                    </div>
                    <div className="flex justify-between text-sm border-b border-red-900/50 pb-2">
                      <span className="text-red-200">Demographic Parity Score:</span>
                      <span className="font-mono font-bold text-red-400">{metrics.clients["Hospital B"]}</span>
                    </div>
                    <div className="flex justify-between text-sm pb-2">
                      <span className="text-red-200">Threshold:</span>
                      <span className="font-mono text-slate-400">0.15</span>
                    </div>
                  </div>
                  <div className="mt-6 inline-block bg-red-600 text-white text-xs font-bold px-3 py-1.5 rounded uppercase tracking-wider shadow-lg shadow-red-500/30">
                    Action: Update Rejected
                  </div>
                </div>
              ) : (
                <div>
                  <h2 className="text-2xl font-bold text-emerald-400 mb-2">SYSTEM BALANCED</h2>
                  <p className="text-slate-400 text-sm">All nodes operating within fairness thresholds.</p>
                  <div className="w-full bg-slate-800 h-2 rounded-full mt-4 overflow-hidden">
                    <div className="bg-emerald-500 h-full w-full animate-pulse opacity-50"></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="space-y-6">
            
            {/* Node Status */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-6 text-slate-400 uppercase text-xs font-bold tracking-widest">
                <Server size={16} /> Hospital Node Status
              </div>
              <div className="space-y-4">
                {/* Hospital A */}
                <div className="flex items-center justify-between p-4 bg-slate-950/50 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
                    <span className="font-medium text-slate-200">Hospital A <span className="text-slate-500 text-xs ml-2">(Fair Data)</span></span>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-950 text-emerald-400 border border-emerald-900">
                    Bias: {metrics.clients["Hospital A"]}
                  </span>
                </div>

                {/* Hospital B */}
                <div className={`flex items-center justify-between p-4 bg-slate-950/50 rounded-lg border transition-all duration-300 ${
                  isBiasAlert ? 'border-red-900/60 bg-red-950/10' : 'border-slate-800 hover:border-slate-700'
                }`}>
                  <div className="flex items-center gap-3">
                    <div className={`h-2 w-2 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.6)] ${isBiasAlert ? 'bg-red-500 animate-ping' : 'bg-emerald-500'}`}></div>
                    <span className="font-medium text-slate-200">Hospital B <span className="text-slate-500 text-xs ml-2">(Skewed)</span></span>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-mono border ${
                    isBiasAlert 
                    ? 'bg-red-950 text-red-400 border-red-900 font-bold' 
                    : 'bg-emerald-950 text-emerald-400 border-emerald-900'
                  }`}>
                    Bias: {metrics.clients["Hospital B"]}
                  </span>
                </div>
              </div>
            </div>

            {/* Logs */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-xl flex flex-col h-[300px]">
              <div className="flex items-center gap-3 mb-4 text-slate-400 uppercase text-xs font-bold tracking-widest">
                <Database size={16} /> Federation Logs
              </div>
              <div className="flex-1 bg-black rounded-lg border border-slate-800 p-4 overflow-y-auto font-mono text-xs leading-relaxed custom-scrollbar shadow-inner">
                {metrics.logs.slice().reverse().map((log, i) => (
                  <div key={i} className={`mb-2 ${log.includes("ALERT") ? "text-red-400 font-bold border-l-2 border-red-500 pl-2" : "text-emerald-400/80"}`}>
                    <span className="text-slate-600 mr-2">[{new Date().toLocaleTimeString()}]</span>
                    {log}
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

export default App;