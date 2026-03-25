import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getHistory } from '../services/api';

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory().then(data => {
      setHistory(data);
      setLoading(false);
    }).catch(console.error);
  }, []);

  if (loading) return <div className="text-gray-400 animate-pulse">Loading history logs...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Scan History</h1>
      <p className="text-gray-400 max-w-2xl">Complete ledger of all prior cargo inspections run through the Intelligence Node. Data is immutable and preserved for compliance review.</p>

      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-900/50 text-gray-400 text-sm uppercase tracking-wider">
                <th className="p-4 font-medium border-b border-gray-700">Scan ID</th>
                <th className="p-4 font-medium border-b border-gray-700">Image Reference</th>
                <th className="p-4 font-medium border-b border-gray-700">Timestamp</th>
                <th className="p-4 font-medium border-b border-gray-700">Risk Assessment</th>
                <th className="p-4 font-medium border-b border-gray-700 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {history.map(scan => (
                <tr key={scan.id} className="hover:bg-gray-750 transition-colors">
                  <td className="p-4 font-mono text-sm text-gray-300">INC-{scan.id.toString().padStart(4, '0')}</td>
                  <td className="p-4 text-sm text-gray-400 truncate max-w-[200px]" title={scan.image_url}>
                    {scan.image_url}
                  </td>
                  <td className="p-4 text-gray-400">{new Date(scan.created_at).toLocaleString()}</td>
                  <td className="p-4 flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      scan.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-500' :
                      scan.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' :
                      'bg-green-500/20 text-green-500'
                    }`}>
                      {scan.risk_level} ({scan.risk_score} pts)
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <Link href={`/results/${scan.id}`} className="text-blue-400 hover:text-blue-300 font-medium text-sm">
                      Full Analysis &rarr;
                    </Link>
                  </td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-gray-500">No activity logs recorded in the database database.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
    </div>
  );
}
