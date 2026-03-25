import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getScanResult } from '../../services/api';
import { ShieldAlert, Crosshair, CheckCircle, Database, AlertCircle, Brain, Layers, Target, Eye, FileText } from 'lucide-react';

export default function ResultDetail() {
  const router = useRouter();
  const { id } = router.query;
  
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    getScanResult(id)
      .then(setData)
      .catch(err => setError(err.message));
  }, [id]);

  if (error) return <div className="text-red-500 p-8 border border-red-500/30 rounded-lg bg-red-500/10">Error: {error}</div>;
  if (!data) return <div className="text-gray-400 animate-pulse">Decrypting intelligence report...</div>;

  const { scan, detections } = data;
  const isHighRisk = scan.risk_level === 'HIGH';

  // Memoize scan and detection derived data
  const vitData = (() => {
    try {
      return scan.vit_analysis ? JSON.parse(scan.vit_analysis) : null;
    } catch (e) {
      return null;
    }
  })();

  const severityColor = (sev) => {
    if (sev === 'HIGH') return 'text-red-500 bg-red-500/10 border-red-500/30';
    if (sev === 'MEDIUM') return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
    return 'text-green-500 bg-green-500/10 border-green-500/30';
  };

  return (
    <div className="max-w-[1600px] mx-auto space-y-10 pb-20 animate-in fade-in duration-700">
      {/* ─── COMMAND CENTER HEADER ─── */}
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6 border-b border-gray-800 pb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border border-blue-500/20">
              Live Intel Report
            </div>
            <span className="text-gray-600 font-mono text-sm tracking-widest">#{scan.id.toString().padStart(6, '0')}</span>
          </div>
          <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">
            Cargo Integrity <span className="text-blue-500">Analysis</span>
          </h1>
          <p className="text-gray-500 mt-2 font-mono text-xs uppercase tracking-widest">
            {new Date(scan.created_at).toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short' })} • SECURE ENCRYPTED CHANNEL
          </p>
        </div>

        <div className="flex gap-4">
          <div className="bg-gray-900/50 p-4 border border-gray-800 rounded-2xl flex items-center gap-4 group hover:border-blue-500/30 transition-all">
            <div className={`p-4 rounded-xl ${scan.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-500 pulse' : 'bg-green-500/20 text-green-500'}`}>
              <ShieldAlert size={28} />
            </div>
            <div className="pr-4">
              <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Assessment</div>
              <div className={`text-2xl font-black uppercase ${scan.risk_level === 'HIGH' ? 'text-red-500' : 'text-green-500'}`}>
                {scan.risk_level} Risk
              </div>
            </div>
          </div>

          <div className="bg-gray-900/50 p-4 border border-gray-800 rounded-2xl flex items-center gap-4">
            <div className="p-4 rounded-xl bg-blue-500/20 text-blue-400">
              <span className="text-2xl font-black">{scan.risk_score}</span>
            </div>
            <div className="pr-4">
              <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Risk AI Score</div>
              <div className="text-2xl font-black text-white italic">/100</div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── ALERT BANNER ─── */}
      {scan.mismatch_found === 1 && (
        <div className="bg-red-500/10 border border-red-500/30 p-6 rounded-2xl flex items-center gap-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-red-500/5 animate-pulse" />
          <AlertCircle size={32} className="text-red-500 shrink-0 relative z-10" />
          <div className="relative z-10">
            <h2 className="text-lg font-black text-red-500 uppercase tracking-tighter italic">CRITICAL CARGO MISMATCH</h2>
            <p className="text-gray-400 text-sm mt-1">
              AI has identified prohibited threat classes within declared category: <span className="text-white font-bold underline">"{scan.declared_cargo}"</span>. Access secondary inspection immediately.
            </p>
          </div>
        </div>
      )}

      {/* ─── MAIN INTELLIGENCE GRID ─── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* LEFT COLUMN: VISUAL ANALYSIS */}
        <div className="xl:col-span-2 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* YOLO View */}
            <div className="group space-y-4">
              <div className="flex items-center justify-between text-[10px] font-bold text-blue-500 tracking-[0.2em] uppercase">
                <span className="flex items-center gap-2"><Crosshair size={14} /> Threat Localizer</span>
                <span className="text-gray-600">Model: YOLOv8s</span>
              </div>
              <div className="aspect-[4/3] bg-gray-950 rounded-2xl border border-gray-800 overflow-hidden shadow-2xl relative">
                <img 
                  src={`http://localhost:5000/uploads/annotated_${scan.filename}`} 
                  onError={(e) => { e.target.src = `http://localhost:5000/uploads/${scan.filename}` }}
                  className="w-full h-full object-contain p-2"
                  alt="YOLO"
                />
              </div>
            </div>

            {/* ViT View */}
            <div className="group space-y-4">
              <div className="flex items-center justify-between text-[10px] font-bold text-purple-500 tracking-[0.2em] uppercase">
                <span className="flex items-center gap-2"><Brain size={14} /> Pattern Analysis</span>
                <span className="text-gray-600">Model: ViT-B/16</span>
              </div>
              <div className="aspect-[4/3] bg-gray-950 rounded-2xl border border-purple-500/20 overflow-hidden shadow-2xl relative">
                <img 
                  src={`http://localhost:5000/uploads/vit_${scan.filename}`} 
                  onError={(e) => { e.target.src = `http://localhost:5000/uploads/${scan.filename}` }}
                  className="w-full h-full object-contain p-2"
                  alt="ViT"
                />
              </div>
            </div>
          </div>

          {/* AI Intelligence Briefing */}
          <div className="bg-gray-900/50 p-8 rounded-3xl border border-gray-800 shadow-xl">
             <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                    <FileText size={20} className="text-blue-400" />
                </div>
                <h3 className="text-sm font-bold text-gray-200 uppercase tracking-widest">Intelligence Briefing</h3>
             </div>
             <p className="text-gray-400 text-lg leading-relaxed font-light tracking-wide italic">
                "{scan.risk_explanation || scan.explanation || "System performing deep structural analysis. No immediate terminal threats detected but caution is advised in internal compartments."}"
             </p>
          </div>
        </div>

        {/* RIGHT COLUMN: DATA METRICS */}
        <div className="space-y-8">
          {/* Anomaly Gauge */}
          <div className="bg-gray-900/80 p-6 rounded-3xl border border-gray-800 shadow-xl">
            <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-6 border-b border-gray-800 pb-4">
                Structural Anomaly Detection
            </div>
            <div className="flex flex-col items-center py-6">
               <div className="relative w-48 h-48 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="96" cy="96" r="88" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-gray-800" />
                    <circle cx="96" cy="96" r="88" stroke="currentColor" strokeWidth="12" fill="transparent" 
                      strokeDasharray={2 * Math.PI * 88}
                      strokeDashoffset={2 * Math.PI * 88 * (1 - (scan.anomaly_score || 0))}
                      className="text-orange-500 transition-all duration-1000 ease-out" 
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                     <span className="text-4xl font-black text-white">{( (scan.anomaly_score || 0) * 100).toFixed(0)}%</span>
                     <span className="text-[10px] text-gray-500 font-bold uppercase tracking-tighter">Variance σ</span>
                  </div>
               </div>
               <p className="text-[10px] text-gray-400 mt-6 text-center italic tracking-wide max-w-[200px]">
                  CNN extraction identified structural fluctuations in cargo arrangement.
               </p>
            </div>
          </div>

          {/* Pattern Breakdown */}
          {vitData && (
            <div className="bg-gray-900/80 p-6 rounded-3xl border border-purple-500/20 shadow-xl overflow-hidden relative">
               <div className="absolute -right-10 -top-10 opacity-10">
                  <Brain size={120} className="text-purple-400" />
               </div>
               <div className="text-[10px] font-black text-purple-500 uppercase tracking-widest mb-4 border-b border-purple-500/20 pb-4">
                  Smuggling Patterns (ViT)
               </div>
               <div className="space-y-3 relative z-10">
                  {vitData.patterns?.slice(0, 3).map((p, i) => (
                    <div key={i} className="flex justify-between items-center text-xs">
                       <span className="text-gray-400">{p.pattern}</span>
                       <span className={`font-bold ${p.severity === 'HIGH' ? 'text-red-500' : 'text-yellow-500'}`}>{p.severity}</span>
                    </div>
                  ))}
               </div>
            </div>
          )}

          {/* Threat List Mini-View */}
          <div className="bg-gray-900/80 p-6 rounded-3xl border border-gray-800 shadow-xl h-full">
            <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4 border-b border-gray-800 pb-4">
                Identified Threats ({detections.length})
            </div>
            <div className="space-y-4 max-h-[300px] overflow-auto pr-2 scrollbar-none">
              {detections.map(d => (
                 <div key={d.id} className="flex items-center justify-between border-b border-gray-800/50 pb-3">
                    <div>
                        <div className="text-sm font-bold text-gray-200 capitalize">{d.object_name}</div>
                        <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mt-1">
                            {d.threat_category}
                        </div>
                    </div>
                    <div className="text-right">
                       <div className="text-xs font-mono text-blue-400">{(d.confidence * 100).toFixed(0)}%</div>
                       <div className="text-[9px] text-gray-600 mt-0.5 font-bold uppercase tracking-tighter">Confidence</div>
                    </div>
                 </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

